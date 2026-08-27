# EXP07 — Vision Operating-Point Safety Trace — Results

**Status: SUCCESS (strong criterion met, with one important correction to H7's framing)**

Interpreter: `/opt/anaconda3/bin/python3` (ultralytics 8.4.14), device mps (Apple M4 Pro).
sure-project git commit at run time: `3c1b9fabf7a5de59e83b81965d1a319498baaec5` (2026-08-26).
Scripts: `exp07_fish_per_frame.py`, `exp07_conf_sweep.py`, `exp07_conf_curve_analysis.py`.
Total wall time: ~57s across all three scripts.

## Open decisions resolved

1. **Direct empirical count vs. independence approximation (recommended primary)**: implemented
   both, with the empirical count (running `best.pt` at the deployed `conf=0.20` on every val
   frame and counting actual zero-detection outcomes) treated as primary, exactly as recommended.
2. **Which confidence thresholds to sweep**: `vision-service/yolo_runner.py` line 44 was read
   directly: `CONF_THRESH = 0.20  # 0.30→0.20: yoğun karelerde recall artışı (daha az kaçan
   balık)` — the deployed threshold is **0.20**, not the design doc's assumed "typical default of
   0.25," and its own comment confirms it was deliberately lowered from 0.30 for recall. The
   sweep was built around this confirmed value: {0.10, 0.15, 0.20 (deployed), 0.25, 0.30, 0.35,
   0.40}.

## 1. Fish-per-frame distribution (from val ground-truth labels)

- 98 val images, 1525 total ground-truth fish → **15.56 fish/frame average**, matching
  MODEL_RAPORU.md's ~15.6 exactly.
- **Minimum fish-per-frame in the val set is k=3.** There are **zero frames with k=0, k=1, or
  k=2** ground-truth fish. Full histogram in `exp07_fish_per_frame_summary.json`.

**This is the single most important and somewhat surprising finding of this experiment**: the
design doc's hypothesis explicitly worried about "a materially sparse subset of frames (1-2 fish)"
making full-frame misses far more probable — but no such frames exist anywhere in the 98-image val
set to check. The dataset simply does not contain a sparse-frame regime to empirically validate
against. This is a **dataset-coverage gap**, distinct from (and in addition to) the original
safety question: the model's behavior on genuinely sparse frames (1-2 fish, which surely occur in
real deployment — a tank being drained, a sick/isolated fish, partial camera occlusion) is
**completely untested** by this val set, in either direction.

## 2. Full-frame-miss rate: empirical (primary) vs. independence approximation (secondary)

**Empirical (primary), at the deployed conf=0.20**: ran `best.pt` on all 98 val frames (all of
which have k≥3 ground-truth fish). **0 / 98 frames (0.0%) had zero detections.** Every single
validation frame produced at least one detection, despite per-instance recall being well below
100%. Detail in `exp07_per_frame_detail.json` (per-frame k and n_detections) and
`exp07_fish_per_frame_summary.json`.

**Independence approximation (secondary, using the MODEL_RAPORU headline recall=0.719)**:
P(full-frame miss | k) = (1−0.719)^k → k=3: 2.2%, k=6: 0.05%, k=9: ~0.001%. Summed over all
98 (k≥3) val frames: **expected 0.053 full-frame misses** — consistent with the observed 0.
Even the *approximation*, before empirical confirmation, already predicted near-zero misses
because no frame in this val set has fewer than 3 fish.

**Extrapolated (untested) risk at low k, for the write-up's honesty**: since no k=1/k=2 frames
exist to test directly, the independence approximation is the *only* available estimate for that
regime, and it should be reported as an untested extrapolation, not a measurement:
  - at k=1, using headline recall 0.719: P(miss) ≈ 28.1%
  - at k=1, using the deployed-operating-point recall 0.782 (see section 3): P(miss) ≈ 21.8%
  - at k=2: ≈7.9% (headline) / ≈4.7% (deployed operating point)

These are not small numbers — if a genuinely sparse (1-2 fish) frame ever occurs in production,
the independence approximation suggests a real, non-negligible chance of a full-frame miss,
**one this val set cannot confirm or refute**. This should be flagged as a specific, quantified
gap in the paper (not just a general caveat), per the design's minimum-viable fallback criterion.

## 3. Confidence-threshold sweep — F1-argmax check, and a correction to H7's framing

Two complementary checks were run:

**(a) `model.val(conf=X)` for X in {0.10,...,0.40}** (`exp07_conf_sweep.py`): found
`box.mp`/`box.mr` **identical** (0.859/0.719) for every conf from 0.10 through 0.30, only
changing once conf exceeded ~0.34. **Methodological finding, worth documenting**: Ultralytics'
`val(conf=X)` does not pin precision/recall to exactly conf=X — `box.mp`/`box.mr` report an
argmax-over-the-retained-curve figure, so passing a low `conf` has no effect on the reported P/R
as long as the true best-F1 point still lies within the retained range. This means **`val(conf=X)`
alone is the wrong tool for asking "what is precision/recall AT the deployed threshold"** — a
trap worth flagging so nobody else reruns into it.

**(b) Reading Ultralytics' fine-grained per-confidence curve directly** (`exp07_conf_curve_analysis.py`,
1000-point curve from a single val() call) — the correct method:

| Confidence | Precision | Recall | F1 |
|---|---|---|---|
| 0.10 | 0.564 | 0.847 | 0.677 |
| 0.15 | 0.655 | 0.813 | 0.726 |
| **0.20 (DEPLOYED)** | **0.720** | **0.782** | **0.750** |
| 0.25 | 0.776 | 0.761 | 0.768 |
| 0.30 | 0.820 | 0.743 | 0.780 |
| 0.35 | 0.851 | 0.725 | 0.783 |
| 0.40 | 0.881 | 0.704 | 0.782 |
| **True F1-argmax (curve peak)** | **0.845** (conf=0.341) | **0.730** | **0.784** |
| **Headline (MODEL_RAPORU, box.mp/mr)** | 0.859 | 0.719 | 0.783 |

**Finding 1 — headline P=0.858/R=0.719 IS (within curve resolution) the true F1-argmax**: the
fine-curve peak sits at conf≈0.341 with F1=0.7835 vs. the headline's F1=0.7827 — a difference of
0.0008, i.e. functionally the same operating point. **H7's confirmation request is satisfied**:
0.858/0.719 is confirmed as (effectively) the F1-argmax, not an arbitrary or mis-selected point.

**Finding 2 — but this is NOT the deployed operating point, and this matters for the safety
narrative.** The actual production system (`yolo_runner.py`, `CONF_THRESH=0.20`) runs at
**P=0.720 / R=0.782**, a substantially different point on the curve: **lower precision, higher
recall** than the headline P/R the paper has been citing as "the" operating point. This is
consistent with the deployed threshold's own inline comment (lowered from 0.30 to 0.20
specifically to raise recall on crowded frames) — it is a deliberate, documented design choice,
not a bug — but it means **the paper's H7 discussion of "recall 0.719" as the number governing
real-world full-frame-miss risk is citing the wrong number**: the number that actually governs
production full-frame-miss risk is the deployed-point recall, **0.782**, which is *higher* (more
reassuring) than 0.719, not lower. Both the empirical zero-miss result (section 2) and this
higher deployed recall point the same direction: **the current safety picture is more reassuring
than a naive reading of "headline recall = 0.719" would suggest**, precisely because production
already runs at a recall-favoring threshold different from the reported academic-style headline
metric.

## Trace to `backend/rules.py`

Confirmed by direct read (`backend/rules.py` lines 69–75): `fish_count == 0` raises `status` to
`"warning"` via `_raise_to(status, "warning")`, with reasoning text "Karede hiç balık tespit
edilmedi (vision servisi arızalı veya sürü dibe çökmüş olabilir)" — i.e. the system is already
designed to treat a full-frame miss as an alarm-worthy anomaly (vision failure or the whole shoal
sitting on the bottom), not to silently ignore it. Given section 2's empirical 0/98 full-frame-miss
result at the deployed threshold, this rule is not currently firing spuriously on any val-set
frame, and — per its own design intent — would correctly flag the genuinely-untested sparse-frame
scenario (section 2's extrapolated ~22% miss risk at k=1) if it ever occurs in production.

## Known Limitations text carried forward

Per MODEL_RAPORU.md: "Kalan zayıf nokta: Recall ~0.72 — yoğun/örtüşen balıklar kaçırılıyor" ("The
remaining weak point: Recall ~0.72 — dense/overlapping fish are missed"). This experiment
confirms the mechanism this traces to (`rules.py`'s `fish_count==0` rule) and refines the
picture: the ~0.72 figure is an academic-style argmax metric, not the production operating point
(which runs at ~0.78 recall); the individual-fish misses this limitation refers to are real, but
did not translate into any full-frame miss across the entire val set at the deployed threshold.

## Verdict against success criteria

**Strong criterion met**: fish-per-frame distribution computed directly from val labels;
full-frame-miss rarity quantified numerically (0/98 empirical, 0.053 expected via approximation);
confidence-threshold sweep run and confirms 0.858/0.719 as (within curve resolution) the true
F1-argmax; H7 stated with confident language above; Known Limitations #2 text carried forward and
traced to `rules.py`. **One correction added beyond the original hypothesis**: H7 as originally
scoped implicitly treated 0.719 as "the" operating recall governing safety risk; this experiment
shows the deployed system actually operates at a different (higher-recall) point on the curve, and
that distinction should be made explicit in the paper's Discussion, not glossed over.

## Files in this run directory

- `exp07_fish_per_frame.py`, `exp07_fish_per_frame_summary.json`, `exp07_per_frame_detail.json`
- `exp07_conf_sweep.py`, `exp07_conf_sweep_summary.json` (fixed-conf val() sweep + the
  argmax-over-retained-curve methodological finding)
- `exp07_conf_curve_analysis.py`, `exp07_conf_curve_summary.json` (fine-grained curve analysis —
  the authoritative numbers for "P/R at a specific confidence")
