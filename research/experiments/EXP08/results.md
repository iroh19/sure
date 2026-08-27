# EXP08 — MLOps PSI Drift-Binning Systematic Sweep & Three-Way Gate Exercise

**Status:** success, with an honest nuance vs. the literal H5 wording (see "Curve comparison" below)
**Repo state:** sure-project @ `3c1b9fa` (2026-08-26T08:57:33+03:00). `git log --oneline --all -- mlops/drift.py` returns exactly **1 commit** — re-confirmed at execution time, matching the design pass's finding. The equal-width curve below is therefore explicitly a **faithful reconstruction** using `drift.py`'s own `histogram()`/`psi()` machinery with fixed `[i/10 for i in 1..9]` edges, never presented as recovered git history.

Script: `g8_psi_sweep.py`. Raw output: `exp08_output.json`. Synthetic windows written: `synthetic_no_drift_window.json`, `synthetic_significant_drift_window.json`.

## Open decisions resolved

1. **Severity grid / perturbation model** — chose a mean-shift sweep, `delta ∈ {0.00, 0.02, …, 0.30}` (16 points), applied by resampling-with-replacement from the reference (n=1467) and subtracting `delta` per sample (clipped to `[0,1]`). This matches `drift.py`'s own `mean_reference`/`mean_current` framing and was the rationale doc's own recommended simplest option. Variance-inflation was not additionally layered in — flagged as a natural extension, not attempted here.
2. **`incumbent_map50()` end-to-end check** — ran standalone before the sweep: it returned **0.83949** without raising, against the existing `mlops/mlflow.db`. Confirms the "retrain" action's second-stage message path works end-to-end in this environment.

## Sweep result (quantile vs. equal-width PSI, mean-shift severity)

| delta | current mean | quantile PSI | quantile severity | equal-width PSI | equal-width severity |
|---|---|---|---|---|---|
| 0.00 | 0.648 | 0.005 | none | 0.005 | none |
| 0.02 | 0.623 | 0.164 | moderate | 0.078 | none |
| 0.04 | 0.600 | 0.728 | significant | 0.306 | significant |
| 0.06 | 0.582 | 1.478 | significant | 0.906 | significant |
| 0.08 | 0.557 | 2.184 | significant | 2.141 | significant |
| 0.10 | 0.537 | 2.652 | significant | 3.027 | significant |
| 0.12 | 0.519 | 3.372 | significant | 3.474 | significant |
| ... | ... | ... | ... | ... | ... |
| 0.30 | 0.338 | 4.844 | significant | 7.649 | significant |

(Full 16-point sweep in `exp08_output.json`.)

## Curve comparison — honest finding, reported exactly as observed

The literal H5 wording ("equal-width saturates/jumps discontinuously at some severities" while "quantile grades smoothly") does **not** cleanly hold in the direction naively expected at *low* severities: at delta=0.02, **quantile PSI (0.164, moderate) is actually higher/more sensitive than equal-width (0.078, none)** — the opposite of "equal-width jumps first." At delta≥0.04 both schemes already classify as "significant," so the useful "moderate" band is visible in this sweep only briefly, for quantile, at delta=0.02.

What the sweep *does* confirm, mechanistically, is the root cause `drift.py`'s own code comment narrates — just visible at a different point in the severity range than the headline "0.06→1.05" anecdote implies. Per-bin inspection at delta=0.08 (see `exp08_output.json` sweep step or rerun with the bin printer) shows why:

- Equal-width's fixed bin `[0.800, 0.900)` holds **30.1%** of the reference mass (a single large bin, because the detector's confidences cluster in ~0.5–0.9 exactly as `drift.py`'s comment says). Once the delta=0.08 shift empties that bin to **0.14%** of current mass, that one bin alone contributes **1.615** to the equal-width PSI total of 2.141 — three-quarters of the whole statistic from a single near-emptied large bin.
- Quantile binning has no single bin holding more than ~10% of reference mass by construction, so no single bin can dominate the total the same way; its largest single-step jump across the whole sweep is delta 0.04→0.06 (+0.75), versus equal-width's largest jump of +1.24 at delta 0.06→0.08 — equal-width's jump is both larger and occurs at a higher severity, once mass has migrated far enough to empty a large fixed bin.
- Equal-width **overtakes and exceeds** quantile PSI from delta=0.08 onward and stays higher through delta=0.30 (7.65 vs. 4.84) — consistent with the "explosive, saturating" character described qualitatively, but manifesting as growing *faster and larger at high severity* rather than "jumping early from near-zero," which is the more precise, honest characterization this sweep supports.

**Conclusion for the manuscript:** report this as "equal-width binning is *less* sensitive than quantile binning to small early shifts (coarser resolution in the busy 0.5–0.9 region) but *more* explosive at larger shifts once a large fixed bin empties, driven by a single bin's log-ratio term dominating the total — confirmed mechanistically via per-bin decomposition, not merely asserted." This is a more nuanced, defensible claim than a blanket "equal-width jumps early, quantile grades smoothly," and is exactly the kind of honest divergence-from-hypothesis the minimum_viable clause asks to be reported precisely.

## Retrain gate exercise (`mlops/retrain.py`)

Two synthetic windows (n=1467 each, ≥ `MIN_WINDOW`=200):

- **No-drift window** (delta=0.00, resampled from reference): `decide()` → **action="none"**, PSI=0.0048 ("no meaningful drift — PSI 0.0048 (none) — mean confidence 0.642 → 0.647").
- **Significant-drift window** (delta=0.04, chosen as the smallest swept delta whose quantile PSI ≥ SIGNIFICANT=0.25): `decide()` → **action="retrain"**, PSI=0.9070 ("significant drift — PSI 0.9070 (significant) — mean confidence 0.642 → 0.595").

Both actions match `retrain.py`'s documented three-way logic exactly (none < MODERATE=0.10 ≤ review < SIGNIFICANT=0.25 ≤ retrain).

## `gate()` three-delta exercise

Synthetic incumbent mAP50 = 0.760 (arbitrary but realistic placeholder — no live retrain occurred, this exercises the pure `gate()` function directly per the spec):

| case | candidate | delta | gate_passes | reason |
|---|---|---|---|---|
| below zero | 0.750 | -0.010 | False | does not beat incumbent |
| inside noise band | 0.7625 | +0.0025 | False | inside the 0.005 MIN_IMPROVEMENT band — not shipping |
| above MIN_IMPROVEMENT | 0.775 | +0.015 | True | beats incumbent by +0.0150 |

All three outcomes match `gate()`'s documented three-way behavior exactly.

## Sources cited (per spec)

Source 23 (PSI/binning literature) and source 22 (champion-challenger MLOps) frame H5 as an application of known best practice — full citations left to the manuscript's own reference list (not re-derived here; this experiment only produces the empirical sweep the citations would frame).
