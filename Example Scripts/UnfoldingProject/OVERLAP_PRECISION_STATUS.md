# Status: are steepest_edge's "overlaps" real, or floating-point noise?

Handoff summary of an unresolved question in the unfolding-overlap research.
Builds on `PIPELINE_AUDIT.md` (read that first for the Sept 2026 pipeline
rebuild: reproducibility fixes, `newton_tol` tightening, the
certified-vs-raw overlap distinction). This file picks up where that left
off, at larger n, where the question got harder rather than easier.

## The research question

Does `steepest_edge` unfolding ever produce a genuine geometric overlap, or
is it structurally protected from doing so (unlike `dfs`/`bfs`, which
overlap constantly)? This is the central open question from the thesis
proposal's unfolding-overlap work.

## What's been run

Three sweeps at n = 800, 1500, 2000 (`methods=['steepest_edge','dfs','bfs']`,
`newton_tol=1e-13`, `n_iterations=1000`), trial counts 50/100/150. Data in
`scaling_sweep_data/quick_n{800,1500,2000}_{trials,pairs}.csv`. Environment
was fixed before these ran (stale `PYTHONPATH` was shadowing the real repo
with an unrelated old checkout -- see git history / prior session; confirmed
fixed, hull generation confirmed bit-reproducible across runs).

**Certified overlap rate (the pipeline's own 10x-noise-floor filter):**

| n | steepest_edge | dfs | bfs |
|---|---|---|---|
| 800 | 0% | 100% | 64% |
| 1500 | 0% | 100% | 100% |
| 2000 | 0% | 100% | 100% |

**Raw overlap rate (`min_plane < 1`, no filtering at all):**

| n | steepest_edge trials affected | total raw dips |
|---|---|---|
| 800 | 0 / 50 | 0 |
| 1500 | 3 / 100 | 3 |
| 2000 | 15 / 150 | 24 |

This is the crux of the current disagreement: **certified says 0% at every
n; raw says a small, growing fraction of trials have `steepest_edge` dipping
below the touching threshold.** The question is whether that raw signal is
real geometry or an artifact of the pipeline's own numerical limits.

## The case for "it's noise" (built so far)

1. **`packing_residual`** = max over every edge in the packing (every pair of
   circles mathematically required to be exactly tangent) of
   `|inversive_distance - 1.0|`. Computed fresh per trial, directly from the
   packing, via `packing_tangency_residual()` in `inversive_distance.py`.
   This is a faithful (not approximate) measurement of how sloppy that
   specific packing's tangencies already are, before any unfolding.

2. **Every one of the 15 n=2000 raw dips has `deficit / packing_residual` ≤
   ~1.14x** -- i.e. the "overlap" is the same size as, or smaller than, the
   packing's own baseline numerical error. (DFS's real overlaps run into the
   thousands-to-millions on this same ratio -- a completely different
   signature.)

3. **Direct pair-level check (not just aggregate comparison):** for the
   worst n=2000 case (trial 135, pair 366-1289), loaded the actual saved
   packing and confirmed:
   - This pair **is a genuine packing edge** (required to be exactly
     tangent), not an unrelated pair that happens to read near 1.0.
   - Its own tangency deviation (`2.4e-6`) is unremarkable: **815 of the
     packing's 5,994 edges** (~14%) have deviation at least half as large.
     It's an ordinary edge in a packing full of edges this far off, not an
     outlier.
   - `sphere` (pre-unfolding distance) and `plane` (post-unfolding distance)
     are nearly identical for every flagged case -- the unfolding barely
     changed the number. A real overlap should show large, consistently
     negative `delta = plane - sphere` (like DFS does); these don't.

4. **Ruled out "just needs tighter convergence":** tested directly --
   `newton_tol` 1e-13 vs 1e-15 (100x tighter target): no change in achieved
   residual. `n_iterations` 1000 vs 5000: no change either. This is a true
   float64 precision ceiling, not an under-converged solve.

## Where this stands / what's NOT settled

The user (lab PI) is not satisfied that this constitutes proof, and that
pushback is fair: everything above is evidence that the noise explanation is
*consistent* and *plausible*, not a demonstration that it's *correct*. In
particular:

- All of this is still argument-from-magnitude ("the effect is the same
  size as known noise"), not a computation of the true answer.
- 15 trials out of 150 (10%) having *some* raw dip, with the rate seemingly
  climbing with n (0% -> 3% -> 10%), reads to the user as a trend that
  deserves harder proof before being dismissed, not just a bigger noise
  floor to point at.

## Concrete next steps discussed (none implemented yet)

In order of rigor (and roughly, of engineering cost):

1. **Perturbation test (cheapest):** re-solve the same flagged seed with a
   perturbation smaller than `packing_residual` applied to the input. If the
   overlap's sign flips or vanishes under a nudge smaller than itself, it
   was never a real, stable effect.
2. **Independent formula cross-check:** recompute the same pair's inversive
   distance via an algebraically different (but equivalent) formula, to
   check whether the result is an artifact of a specific cancellation
   pattern in the current formula.
3. **High-precision re-solve (mpmath, ~50 decimal digits):** rewrite just
   `newton_packing` and `canonical_spherical_layout` (not the whole
   pipeline -- combinatorics stay the same, only coordinates need
   re-deriving) in arbitrary precision, for only the ~18 flagged seeds. Cuts
   the noise floor by ~30 orders of magnitude. Not a formal proof, but would
   almost certainly be decisive in practice. Estimated cost: a real but
   bounded engineering task (two functions, not the whole codebase),
   expected to run much slower per-trial (plan for minutes, not seconds) but
   only needs to run on a handful of seeds.
4. **Interval arithmetic (most rigorous):** track provable error bounds
   through the computation (e.g. `mpmath.iv`) instead of point values --
   produces a certified bracket around the true answer. The only option
   that actually *proves* the sign rather than making the evidence stronger.
   More implementation work than #3.

No decision has been made on which to pursue; the user wants to think it
through further before committing engineering time.

## Key files

- `PIPELINE_AUDIT.md` -- the original Sept 2026 pipeline rebuild writeup
  (read this first for background).
- `run_scaling_sweep.py` -- the two-stage sweep driver (known-bad methods
  `join_bfs`/`join_dfs`/`normal_min`/`normal_max` are excluded -- they hang,
  unrelated bug, not investigated).
- `analyze_sweep_results.py` -- generates summary tables + PNG charts from
  `scaling_sweep_data/*_trials.csv`.
- `check_overlap_certification.py` -- labels every file in
  `overlapping_packings/` as REAL or noise by cross-referencing the trial
  CSVs (raw saves include noise-level dips, not just certified ones).
- `unfolding_overlap_analysis.ipynb` -- the full interactive analysis
  (certified + raw summary tables, the sphere-vs-plane cross-check for every
  raw dip, overlap-rate charts, steepest_edge decay chart). Open with the
  `koebepy (.venv)` Jupyter kernel. Re-run top to bottom to refresh against
  new sweep data.
- `scaling_sweep_data/*_trials.csv`, `*_pairs.csv` -- the raw data behind all
  of the above.
- `overlapping_packings/*.pkl` -- actual packing+unfolding geometry for
  every raw overlap (not just certified), loadable with `pickle`.

## Environment notes (for a fresh session)

- Repo: `/Users/joedirocco/Documents/Research/koebepy`, venv at
  `koebepy/.venv`. `koebepy` is pip-installed editable in that venv.
- A stale `PYTHONPATH` in `~/.zshrc` that shadowed this repo with an
  unrelated old checkout was removed earlier in this project -- if `import
  koebe` ever resolves to a path outside this repo again, check
  `echo $PYTHONPATH` first before debugging anything else.
- Jupyter kernel `koebepy-venv` ("koebepy (.venv)") is registered against
  this venv and has pandas/matplotlib/nbformat/etc. installed.
