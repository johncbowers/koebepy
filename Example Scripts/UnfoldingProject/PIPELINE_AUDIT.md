# Pipeline Audit — September 2026

Notes on why the measurement pipeline was rebuilt at the start of Fall 2026, and
what changed. Written after auditing `03fefbf "test: found counterexamples for
steepest edge"` against the state of the harness at `e39eb68`.

## Summary

The two steepest-edge "counterexamples" committed in `03fefbf` do not survive a
tighter circle-packing solve. They are floating-point artifacts, not geometry.
Steepest edge has still never produced a genuine overlap in this pipeline.

Three defects in the harness allowed them through. All three are fixed here.

---

## 1. Reproducibility controls were lost in a merge

`6b459ca "fix: fixed merge conflict"` resolved in favor of the incoming branch and
deleted three things added in `e39eb68`:

- `_clone_packing_for_method()`
- `trial_seed_override`
- `isolate_packing_per_method`

(These were necessary but, as section 4 shows, not sufficient.)

These were not cosmetic. The packing really is mutated across methods:

- `join_unfolding_algorithms.py` writes `edge.key` onto `packing.edges` in
  `shortest_paths_unfolding` (L116-120).
- `least_cost_paths_unfolding` calls `random()` for tie-breaking (L80, L99),
  consuming the **global** `random` module state.

So within a trial, each method's result depended on which methods ran before it.
That is the cause of the "this overlapping does not happen every time" note left
at the bottom of `inversive_distance.py`.

**Fixed:** all three restored. Additionally, the global RNG is now re-seeded
deterministically per `(trial_seed, method_name)` via `_method_seed()`, so a
method's stream no longer depends on the methods preceding it in the list. Adding
or removing a method from `methods=[...]` no longer perturbs the others.

## 2. Layout iterations were hardcoded

`coin_unfolding_modular.py` had `canonical_spherical_layout(packing, n_iterations=20)`
hardcoded, while `compare_methods` still passed `n_iterations=1000`, which was
silently discarded. Every one of the 1,121 steepest-edge trials ran at 20.

**Fixed:** the parameter is honored again.

(For the record: this was *not* what caused the false counterexamples. Re-running
them at 1000 layout iterations changed nothing. It is fixed because a parameter
that is accepted and ignored will cause a different bug later.)

## 3. Overlap detection was far below the precision of the input

`find_overlapping_pairs` flags an overlap at `sum_radii - 1e-10 > distance`. The
packings were not accurate to anywhere near 1e-10.

`min_sphere` in the trial CSV is the smallest inversive distance among non-tree
pairs **in the packing itself**. Packed circles are tangent or disjoint, so it
should be >= 1. Its deficit below 1 is a direct readout of the packing's own
tangency error:

| n   | trials with `min_sphere < 1` | median deficit | worst deficit |
|-----|------------------------------|----------------|---------------|
| 10  | 95/100                       | 8.6e-14        | 3.1e-09       |
| 100 | 101/101                      | 1.2e-09        | 1.0e-05       |
| 350 | 100/100                      | 9.8e-08        | 5.7e-05       |
| 500 | 120/120                      | 1.8e-07        | 9.2e-05       |

Every trial at n >= 50 has a packing whose own circles numerically overlap, by
three to seven orders of magnitude more than the detection threshold.

### The two counterexamples, re-run from their logged seeds

```
n=450 trial66 (seed 7006600157398821403)
  as-run    newton=3e-8   layout=20     min_plane deficit 7.67e-06   min_sphere deficit 9.05e-06   overlaps: 2
  layout++  newton=3e-8   layout=1000   min_plane deficit 7.65e-06   min_sphere deficit 9.00e-06   overlaps: 2
  newton++  newton=1e-13  layout=1000   min_plane SURPLUS 9.03e-06   min_sphere deficit 6.42e-07   overlaps: 0

n=350 trial50 (seed 5014809394238524692)
  as-run    newton=3e-8   layout=20     min_plane deficit 1.36e-04   min_sphere deficit 5.73e-05   overlaps: 2
  layout++  newton=3e-8   layout=1000   min_plane deficit 1.36e-04   min_sphere deficit 5.71e-05   overlaps: 2
  newton++  newton=1e-13  layout=1000   min_plane SURPLUS 3.35e-05   min_sphere deficit 7.97e-08   overlaps: 0
```

Both vanish under a tighter Newton solve. Penetration depths were 4.5e-09 and
2.1e-07 against circle radii of ~0.001-0.005, i.e. 6e-06 and 9e-05 *relative*. In
the n=450 case the packing's own tangency violation (9.0e-06) was larger than the
alleged plane overlap (7.7e-06) — the "overlap" was smaller than the error bar on
the input.

**Fixed, three ways:**

- `newton_packing` tolerance default tightened from `3e-8` to `1e-13` in
  `generate_coin_polygon_orick`, now exposed as `newton_tol`.
- New `packing_tangency_residual(packing)` measures the packing's own worst
  tangency error. It is recorded per trial as `packing_residual` in the CSV.
- Overlaps are now classified. `num_overlappings` keeps its old meaning (raw
  geometric test, backward compatible with existing CSVs).
  `num_overlappings_certified` counts only overlaps whose inversive-distance
  deficit exceeds `overlap_safety_factor * packing_residual` (default 10x).
  **Only certified overlaps should be treated as real.**

---

## 4. Seeded runs were not reproducible at all (root cause, library-level)

Restoring `trial_seed_override` was not enough: replaying a seed still produced a
different polyhedron. Bisecting the generation pipeline located the cause in the
library itself, in `koebe/algorithms/incrementalConvexHull.py::addPoint`:

```python
shadowBoundaryDarts = [dart for dart in shadowDarts if dart.twin in visibleDarts]
```

`shadowDarts` is a `set` of `Dart` **objects**. Python hashes objects by identity,
so iteration order follows memory addresses and varies between runs — and between
allocations inside a single process. That order decides the order in which new
faces and darts are appended to the DCEL, which rotates every vertex's neighbor
list.

Measured before the fix: the same seed produced hulls whose neighbor lists were
cyclic rotations of each other (`v1: [16,37,3,35]` vs `[37,3,35,16]`). Since DFS
walks `v.neighbors()` in order, 14 of 40 vertices ended up with different parents,
and `min_plane` moved from 1.0395 to 1.1073 — a completely different unfolding
from an identical seed.

This is the actual source of the "this overlapping does not happen every time"
note. It also means `trial_seed_override`, the saved `overlapping_packings/`
seeds, and any attempt to re-verify a reported result could never have worked
reliably before now.

**Fixed:** iterate `ch.darts` instead. At that point in `addPoint`, `ch.darts` has
just been filtered to exactly the shadow darts, so the change is semantically
identical but order-stable. Verified: hull generation, the full packing pipeline,
and end-to-end trial metrics are now bit-reproducible across runs.

> This is a change to Dr. Bowers' library rather than to our scripts, and it
> affects every consumer of `incrConvexHull`, not just this project. It should be
> reviewed before it goes anywhere near master.

### Consequence: pre-fix seeds no longer replay

Because the fix changes the order in which hull faces are built, a given seed now
produces a *different* polyhedron than it did before. Seeds recorded in the
existing CSVs and in `overlapping_packings/*_metadata.txt` will not reproduce
their original geometry. The archived `.pkl` files are unaffected — they store the
geometry directly and remain valid.

## 5. Analysis pipeline could not run headless

`coin_unfolding_modular.py` and `inversive_distance.py` imported
`koebe.graphics.flask.multiviewserver` at module scope, so the entire analysis
pipeline required `flask` — which is not installed in `.venv`. Large batch runs
could not execute without a display stack.

**Fixed:** visualization imports are now lazy, pulled in only when a `visualize_*`
function is actually called.

---

## Consequence for the usable range of n

The margin being measured and the noise floor are converging:

- Steepest-edge safety margin (`min_plane - 1`) decays as **n^-2**
  (log-log slope -1.996 from n=10 to n=500).
- Packing tangency error *grows* with n.

At n=500 the 1st-percentile margin is 8.8e-06 while the worst packing residual is
9.2e-05. The tail of the signal has already dropped below the tail of the noise.
That is precisely why false positives appeared at n=350 and n=450 and not earlier.

With the old `newton_tol=3e-8`, the instrument topped out around **n ~ 300**.
Anything reported beyond that was unsupported. The tightened tolerance and the
`packing_residual` column exist so this failure mode is visible in the data
instead of silent.

## Next experiment: does steepest edge ever overlap?

Steepest edge's safety margin (`min_plane - 1`, how close the tightest pair comes
to touching) shrinks as roughly **n^-2** — 10x more faces, ~100x less margin:

| faces | median margin |
|-------|---------------|
| 10    | 5.7e-01       |
| 100   | 6.0e-03       |
| 500   | 2.3e-04       |

(Log-log slope -1.996 from n=10 to n=500. Measured on the *old* pipeline, so
confirming it on the fixed code is step one.)

The margin is shrinking, but shrinking is not the same as crossing zero. Two
possibilities, and they need different evidence:

- **No structure:** the per-pair margin distribution has positive density as
  margin -> 0. Then nothing holds pairs apart and a large enough n must produce
  an overlap. Predict where, then go find it.
- **Structural rigidity:** the distribution thins out and vanishes short of zero.
  Something actively repels pairs from tangency, and that repulsion is a theorem.

**Watching for a crossing does not decide between them.** The margin is a minimum
over ~n^2/2 pairs, so the longer you look the worse a minimum you find. "1000
trials at n=300, no overlap" is weak evidence — 10,000 might have turned one up.
The statistic is confounded by how long you looked.

What decides it is the **shape of the left tail** of the per-pair margin
distribution, which is why `save_pair_data` was added (see below).

### Running the sweep

```python
for n in (25, 50, 100, 150, 200, 250, 300):
    compare_methods(
        methods=["steepest_edge", "dfs", "bfs"],
        n_points=n, n_iterations=500, trials=300,
        newton_tol=1e-13,
        save_trial_data=True, trial_data_filename="sweep_trials.csv",
        save_pair_data=True,  pair_data_filename="sweep_pairs.csv",
        pair_tail_size=200,
        save_overlapping_decls=True, visualize_first_overlap=False,
        run_id=f"sweep_{n}",
    )
```

Stay at or below n ~ 300; `packing_residual` tells you per trial whether you are
still above the noise floor. Budget roughly 6-8s per trial at n=200, nearly all of
it in `canonical_spherical_layout`.

### What `save_pair_data` collects

`track_inversive_pairs` already computed a margin for every pair; `compare_methods`
was discarding all of it and keeping five summary numbers. `save_pair_data=True`
now writes the `pair_tail_size` pairs closest to overlapping per (trial, method)
to `pair_margins.csv`. Only the tail is kept — at n=300 the full set would be
~45k rows per trial per method.

Columns: `run_id, trial_seed, trial, method, n_points, total_pairs,
packing_residual, i, j, sphere, plane, margin, delta, depth_bin, order_bin`

- `margin = plane - 1` — below 0 means those two coins overlap
- `delta = plane - sphere` — below 0 means unfolding *decreased* inversive distance
- `depth_bin` / `order_bin` — where in the unfolding tree the pair sits

Histogram `margin` near zero: density surviving to 0 supports the first
hypothesis, density vanishing supports the second.

One early observation worth checking at scale: in small test runs the tightest
pairs all have `sphere == 1`, i.e. they are adjacent faces that are not tree
edges, which makes `margin` and `delta` coincide. If that holds generally, the
left tail is entirely about adjacent pairs and the analysis narrows considerably.

## Re-running old results

Any conclusion drawn from `n_points_data/unfolding_method_metrics.csv` rows at
n >= 300 should be regenerated before use. The n <= 200 rows are fine.
