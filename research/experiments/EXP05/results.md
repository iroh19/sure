# EXP05 — Vision Dataset Train/Val Leakage Audit — Results

**Status: PARTIAL SUCCESS (minimum_viable met, strong NOT met)**

Interpreter: `/opt/anaconda3/bin/python3` (has PIL 12.0.0, numpy 2.3.5; `imagehash` NOT
installed, confirmed via failed import — inline aHash/dHash implemented instead).
sure-project git commit at run time: `3c1b9fabf7a5de59e83b81965d1a319498baaec5` (2026-08-26).
Script: `exp05_leakage_audit.py`. Wall time: 5.9s.

## Open decisions resolved

1. **Filename source-identity encoding (open_decision #1).** `data/sure_dataset/{train,val}/images`
   is a mix of `videoN_frame_MMMM.jpg` (N in 1..9) and plain `frame_MMMM.jpg` (contiguous
   range 0000–0034). The plain-named files are byte-identical (md5-confirmed) to files of the
   same name under `data/frames/` and form one contiguous frame-index run, so they were
   treated as a single pooled source `frame_source0`, distinct from `video1`..`video9`.
2. **imagehash availability (open_decision #2).** Not installed in the anaconda env
   (`ModuleNotFoundError`). Implemented a minimal 64-bit average-hash (aHash) and 64-bit
   difference-hash (dHash) inline using only PIL + numpy, per the design doc's own fallback plan.

## Findings

**1. Source-group (video-level) collisions: 6 of 10 groups appear in both splits.**
`frame_source0`, `video2`, `video4`, `video5`, `video6`, `video7` each have images in both
train and val; `video1`, `video3`, `video8`, `video9` are train-only. This by itself is not
proof of leakage (splitting frames of the same clip across train/val is a real methodological
choice, not automatically wrong) — but it is the necessary precondition for near-duplicate
leakage, so it triggered the deeper checks below.

**2. Exact frame-index overlap: 0.** Within every colliding group, train and val use
completely disjoint frame indices (e.g. video7: train indices 0–259, val indices 1–246, zero
exact overlaps). This confirms the split is **not** the ogretmen-style "same file in both
splits" leak — it is an **interleaved split of a continuous video**, e.g. video7 train has
frame 23, val has frame 24.

**3. Perceptual-hash near-duplicate check (primary method, per resolved open_decision #1) found
real near-duplicates crossing the split, concentrated at small frame-index gaps:**

| aHash/dHash threshold (bits of 64) | candidate near-duplicate pairs |
|---|---|
| ≤5 (very tight, ~92%+ bit agreement) | **32** |
| ≤10 | 202 |
| ≤16 (loose) | 902 |

Minimum distance found across all within-source-group train/val pairs: **2/64 bits** (i.e.
96.9% of hash bits identical) — e.g. `video7_frame_0023.jpg` (train) vs. `video7_frame_0024.jpg`
(val), adjacent frames of the same clip.

At the strict threshold (≤5 bits), 14 of the 32 candidate pairs have a frame-index gap of 1
(immediately adjacent frames of the same source video, e.g. train frame N against val frame
N±1) — the textbook video-near-duplicate-leakage pattern. Full pair list with per-pair distances
is in `near_duplicate_pairs_full.json`; the 32 strict-threshold hits are also embedded in
`exp05_summary.json["strict_threshold_hits_detail"]`.

**4. Positive-control sanity check passed.** `data/ogretmen.yaml` confirms `train:` and `val:`
point at the byte-identical folder — the method's source-group logic would trivially catch this
(100% collision), confirming the detection method works on a known-positive case. `ogretmen_dataset`
is a separate dataset folder from `sure_dataset` and is not part of the 412/98 split audited here.

## Verdict against success criteria

- **Strong criterion** ("zero cross-split leakage beyond the already-caught ogretmen case") is
  **NOT met**: 32 near-duplicate candidate pairs at a strict 5-bit threshold, with a clear
  temporal-adjacency mechanism (14 of them are literally adjacent frame indices of the same video).
- **Minimum-viable criterion** ("if further leakage IS found, report exactly which images/videos
  are affected and state a corrected, caveated headline number") **is met** by this report: the
  affected videos are video2, video4, video5, video6, video7 (and the un-numbered `frame_source0`
  group); the exact 32 file pairs are enumerated in the summary JSON.

## Implication for the paper's headline vision numbers

This does **not** mean mAP50=0.840/precision=0.858/recall=0.719 are as badly compromised as the
ogretmen case (mAP50=0.918, invalidated), because: (a) no exact duplicate frames exist across the
split (0 exact-index overlaps), and (b) only 32 of 412×98-scoped-to-6-groups possible pairs are
near-duplicates at a strict threshold, i.e. a small fraction of the 98 val images (up to ~14-28
distinct val images out of 98, depending on how many strict hits share a val file — see JSON) have
a near-duplicate counterpart in train. But it does mean the headline recall/precision/mAP50 figures
should be reported with an explicit caveat: **"a small number of validation frames (≈14–32,
concentrated in video6/video7) are temporally-adjacent near-duplicates of training frames from the
same clip; this may cause a modest, unquantified optimistic bias in the reported val metrics beyond
what a fully clip-disjoint split would show."** A rigorous fix (re-splitting by whole video/clip)
was out of scope for this audit (would require retraining) and is recommended as future work, not
executed here.
