"""
Two-stage sweep for the "does steepest edge ever overlap?" question, run on
the post-audit pipeline (fixed hull ordering, newton_tol=1e-13, certified
overlap classification). See PIPELINE_AUDIT.md for background.

IMPORTANT: run this with a clean environment (no stale PYTHONPATH). From the
repo root's venv:

    cd "Example Scripts/UnfoldingProject"
    nohup ../../.venv/bin/python -u run_scaling_sweep.py > scaling_sweep.log 2>&1 &

Then watch progress with:  tail -f scaling_sweep.log
And check it's still alive with:  jobs -l   (or `ps aux | grep run_scaling_sweep`)

Stage A (VALIDATE) re-runs the same n-range the old pre-fix campaign covered
(up to n=500, where the false "counterexamples" showed up) with the broader
method set, so we can tell whether the n^-2 margin-decay trend and the
zero-real-overlap result for steepest_edge survive under the fixed pipeline.

Stage B (PUSH) goes past every n this project has ever run steepest_edge at,
using only the three cheap methods (steepest_edge/dfs/bfs -- the O(n log n)
ones), to look for where (if anywhere) the margin actually crosses zero.
Every trial prints packing_residual so you can see live whether a given n is
still above the noise floor -- if worst-case residual starts approaching the
certified-overlap threshold (10x residual), treat further n as unsupported by
this tolerance rather than pushing blindly higher.

Both stages write to scaling_sweep_data/, and any CERTIFIED overlap trips
save_overlapping_decls, dropping packing+unfolding .pkl + metadata into
overlapping_packings/ for later inspection.
"""

import time

from inversive_distance import compare_methods

OUT_DIR = "scaling_sweep_data"

# Methods that are a single O(n log n) tree build -- safe at any n we'll use.
CHEAP_METHODS = ["steepest_edge", "dfs", "bfs"]

# Adds the other join-tree baselines. Still O(n log n) each individually.
# Excludes shortest_shortest_paths / longest_shortest_paths: those run a full
# shortest_paths build from EVERY vertex (O(n^2 log n)) and get expensive
# fast -- only include them if you drop n back down to <=300 or so.
#
# Also excludes join_bfs/join_dfs and normal_min/normal_max: confirmed by a
# smoke test (n=10, 1 trial) to hang -- one of them pegs a CPU core
# indefinitely even on a trivial graph. That's a bug in
# join_unfolding_algorithms.py (whatever_first_search_unfolding /
# normal_order_unfolding), not a performance issue -- it needs to be fixed in
# that file before those method names are usable here. Not attempted as part
# of this sweep; flagging so it doesn't silently eat compute time.
BROAD_METHODS = CHEAP_METHODS + [
    "shortest_paths", "min_degree_shortest_paths", "max_degree_shortest_paths",
]

# --- Stage A: validate against the old (pre-fix) n-range -------------------
VALIDATE_NS = [10, 50, 100, 200, 300, 350, 450, 500]
VALIDATE_TRIALS = 150          # lower than the audit's 300 to keep runtime sane;
                                 # bump up later once you've confirmed nothing broke.
VALIDATE_ITERATIONS = 1000

# --- Stage B: push past the old max (n=500) ---------------------------------
PUSH_NS = [600, 800, 1000, 1500, 2000]
PUSH_TRIALS = 100
PUSH_ITERATIONS = 1000


def run_stage(label, ns, trials, n_iterations, methods, filename_prefix):
    for n in ns:
        t0 = time.time()
        print(f"\n########## STAGE {label}  n={n}  trials={trials}  methods={methods} ##########", flush=True)
        compare_methods(
            methods=methods,
            n_points=n,
            n_iterations=n_iterations,
            trials=trials,
            newton_tol=1e-13,
            overlap_safety_factor=10.0,
            isolate_packing_per_method=True,
            visualize_first_overlap=False,
            visualize_each_trial=False,
            visualize_trial_packing_each_trial=False,
            save_overlapping_decls=True,
            save_trial_data=True,
            trial_data_output_dir=OUT_DIR,
            trial_data_filename=f"{filename_prefix}_trials.csv",
            save_pair_data=True,
            pair_data_filename=f"{filename_prefix}_pairs.csv",
            pair_tail_size=500,
            run_id=f"{filename_prefix}_n{n}",
        )
        print(f"########## STAGE {label}  n={n} done in {time.time() - t0:.1f}s ##########", flush=True)


if __name__ == "__main__":
    overall_start = time.time()

    run_stage("A-VALIDATE", VALIDATE_NS, VALIDATE_TRIALS, VALIDATE_ITERATIONS,
               BROAD_METHODS, "validate")

    run_stage("B-PUSH", PUSH_NS, PUSH_TRIALS, PUSH_ITERATIONS,
               CHEAP_METHODS, "push")

    print(f"\nTOTAL WALL TIME: {(time.time() - overall_start)/3600:.2f} hours", flush=True)
