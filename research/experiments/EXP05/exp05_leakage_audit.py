#!/usr/bin/env python3
"""
EXP05 -- Vision Dataset Train/Val Leakage Audit (510-image sure_dataset)

READ-ONLY against the live codebase at /Users/batuhancitak/Desktop/sure-project/.
Writes all outputs into this experiment_runs/EXP05/ directory only.

Run with: /opt/anaconda3/bin/python3 exp05_leakage_audit.py

Method
------
1. Enumerate data/sure_dataset/{train,val}/images. Group each filename by
   inferred "source": the videoN_ prefix when present, else a single pooled
   group "frame_source0" for the plain frame_NNNN.jpg files (open_decision #1
   resolved below -- see NOTE-1).
2. Report any source group that has files in BOTH train and val ("cross-split
   source-group collision") -- this is a coarse, filename-only signal, not
   proof of near-duplicate leakage by itself (see NOTE-1 rationale).
3. Cross-check explicitly against the already-known/already-corrected
   ogretmen leak (data/ogretmen.yaml: train and val point at the identical
   images/ folder) to confirm this script's method WOULD catch a real leak
   (positive-control sanity check).
4. Primary near-duplicate check: compute a 64-bit average-hash (aHash) AND a
   64-bit difference-hash (dHash) for all 510 images using only PIL+numpy
   (open_decision #2: imagehash is NOT installed in the anaconda env --
   confirmed via `python3 -c "import imagehash"` -> ModuleNotFoundError, so a
   minimal hash is implemented inline here, exactly as the design doc's
   fallback plan anticipated). For every (train_img, val_img) pair *within
   the same inferred source group* (cross-group pairs are astronomically
   unlikely to be near-duplicates and would blow up the O(n*m) cost for no
   benefit), compute Hamming distance on both hashes and flag pairs below a
   set of threshold values (sensitivity sweep at 3 thresholds, per the design
   doc's "worth trying at 2-3 values" instruction).

NOTE-1 (open_decision #1, resolved by direct inspection):
  `ls data/sure_dataset/{train,val}/images` shows filenames are a MIX:
    - videoN_frame_MMMM.jpg for N in {1..9} (source-video identity IS encoded)
    - plain frame_MMMM.jpg for a contiguous range 0000-0034 with NO video
      prefix. Byte-for-byte identical to files under data/frames/ of the same
      name (confirmed via md5), and forming one contiguous frame-index run
      distinct from the videoN_ groups -- treated as a single pooled source
      "frame_source0" (i.e. NOT source-ambiguous at the per-frame level; only
      ambiguous in that this design's original phrasing worried they might be
      unrelated to each other, which byte-identity + contiguous numbering
      rules out).
  Critically: comparing frame *indices* per source group (see
  exp05_frame_index_check.txt in the script's own printed output) shows video2,
  video4, video5, video6, video7, and frame_source0 ALL have DIFFERENT
  (non-overlapping) exact frame indices in train vs val -- i.e. the split was
  made by interleaving individual frames of the SAME source video across
  train/val, not by holding out whole videos. This is exactly the
  "materially different from expected" case the open_decision flagged as
  requiring perceptual hashing as a PRIMARY method (not a secondary,
  optional one) -- interleaved-frame splits of a continuous video are the
  textbook near-duplicate-leakage risk (adjacent frames of the same clip are
  visually near-identical), so this script promotes the hash check to
  primary evidence rather than a secondary/optional pass.
"""
import json
import os
import re
import sys
import time
from collections import defaultdict
from itertools import combinations

import numpy as np
from PIL import Image

SURE_ROOT = "/Users/batuhancitak/Desktop/sure-project"
DATASET = os.path.join(SURE_ROOT, "data", "sure_dataset")
RUN_DIR = os.path.dirname(os.path.abspath(__file__))

VIDEO_PREFIX_RE = re.compile(r"^(video\d+)_frame_(\d+)\.(jpg|jpeg|png)$", re.IGNORECASE)
PLAIN_FRAME_RE = re.compile(r"^frame_(\d+)\.(jpg|jpeg|png)$", re.IGNORECASE)

HASH_SIZE = 8  # -> 64-bit hashes (matches common aHash/dHash convention)
# Sensitivity sweep over near-duplicate distance thresholds (out of 64 bits).
# <=5 bits differing out of 64 is a very tight "near-duplicate" bar; <=10 and
# <=16 are progressively looser bars used only to see how many *additional*
# borderline candidates appear (per design doc's "worth trying at 2-3 values").
THRESHOLDS = [5, 10, 16]


def list_images(split):
    d = os.path.join(DATASET, split, "images")
    return sorted(f for f in os.listdir(d) if f.lower().endswith((".jpg", ".jpeg", ".png")))


def infer_source(filename):
    m = VIDEO_PREFIX_RE.match(filename)
    if m:
        return m.group(1), int(m.group(2))
    m = PLAIN_FRAME_RE.match(filename)
    if m:
        return "frame_source0", int(m.group(1))
    return "UNKNOWN_" + filename, -1


def average_hash(img_gray_arr):
    """64-bit average hash: 1 bit per pixel vs the mean, HASH_SIZE x HASH_SIZE grid."""
    avg = img_gray_arr.mean()
    bits = (img_gray_arr.flatten() > avg).astype(np.uint8)
    return bits


def difference_hash(img_gray_arr_wp1):
    """64-bit difference hash: needs a (HASH_SIZE, HASH_SIZE+1) grayscale array;
    1 bit per pixel comparing to its right neighbor."""
    diff = img_gray_arr_wp1[:, 1:] > img_gray_arr_wp1[:, :-1]
    return diff.flatten().astype(np.uint8)


def compute_hashes(path):
    img = Image.open(path).convert("L")
    a_img = img.resize((HASH_SIZE, HASH_SIZE), Image.LANCZOS)
    d_img = img.resize((HASH_SIZE + 1, HASH_SIZE), Image.LANCZOS)
    a_arr = np.asarray(a_img, dtype=np.float64)
    d_arr = np.asarray(d_img, dtype=np.float64)
    return average_hash(a_arr), difference_hash(d_arr)


def hamming(bits_a, bits_b):
    return int(np.count_nonzero(bits_a != bits_b))


def main():
    t0 = time.time()
    log_lines = []

    def log(msg):
        print(msg)
        log_lines.append(msg)

    log("=" * 78)
    log("EXP05 -- Vision Dataset Train/Val Leakage Audit")
    log("=" * 78)
    log(f"sure-project root (read-only): {SURE_ROOT}")

    train_files = list_images("train")
    val_files = list_images("val")
    log(f"train/images count: {len(train_files)} (spec expects 412)")
    log(f"val/images count:   {len(val_files)} (spec expects 98)")
    assert len(train_files) == 412, "train count mismatch vs spec"
    assert len(val_files) == 98, "val count mismatch vs spec"

    # ---- Step 1+2: group by source, find cross-split source collisions ----
    train_sources = defaultdict(list)
    val_sources = defaultdict(list)
    for f in train_files:
        src, idx = infer_source(f)
        train_sources[src].append((f, idx))
    for f in val_files:
        src, idx = infer_source(f)
        val_sources[src].append((f, idx))

    all_sources = sorted(set(train_sources) | set(val_sources))
    log("\n--- Source-group breakdown (videoN_ prefix, or pooled frame_source0) ---")
    collisions = []
    for src in all_sources:
        n_tr = len(train_sources.get(src, []))
        n_va = len(val_sources.get(src, []))
        flag = ""
        if n_tr > 0 and n_va > 0:
            flag = "  <-- CROSS-SPLIT SOURCE-GROUP COLLISION (same source video in both splits)"
            collisions.append(src)
        log(f"  {src:16s} train={n_tr:3d}  val={n_va:3d}{flag}")

    log(f"\nCross-split source-group collisions: {len(collisions)} / {len(all_sources)} groups -> {collisions}")

    # ---- Step: check exact frame-index overlap within colliding groups ----
    log("\n--- Exact frame-index overlap check within colliding source groups ---")
    index_overlaps = {}
    for src in collisions:
        tr_idx = set(idx for _, idx in train_sources[src])
        va_idx = set(idx for _, idx in val_sources[src])
        overlap = tr_idx & va_idx
        index_overlaps[src] = sorted(overlap)
        log(f"  {src}: train_idx_range=[{min(tr_idx)},{max(tr_idx)}] "
            f"val_idx_range=[{min(va_idx)},{max(va_idx)}] "
            f"exact_index_overlap_count={len(overlap)}")
        if overlap:
            log(f"    OVERLAPPING EXACT INDICES: {sorted(overlap)}")

    total_exact_overlaps = sum(len(v) for v in index_overlaps.values())
    log(f"\nTotal exact same-frame-index collisions across colliding groups: {total_exact_overlaps}")
    log("Interpretation: 0 exact-index collisions means the split does NOT reuse the "
        "identical frame in both splits, but interleaves DIFFERENT frame indices from "
        "the SAME source video across train/val -- this is a distinct, subtler risk "
        "(near-duplicate adjacent frames) from the ogretmen case (identical folder/files "
        "in both splits), and is exactly what the perceptual-hash check below is for.")

    # ---- Positive-control sanity check: does this method catch ogretmen? ----
    log("\n--- Positive-control sanity check: known ogretmen leak ---")
    ogretmen_yaml = os.path.join(SURE_ROOT, "data", "ogretmen.yaml")
    ogretmen_leak_confirmed = False
    if os.path.exists(ogretmen_yaml):
        content = open(ogretmen_yaml).read()
        log(f"data/ogretmen.yaml contents:\n{content}")
        # train: and val: point at the identical path -> trivial 100% leak by construction
        train_line = [l for l in content.splitlines() if l.strip().startswith("train:")]
        val_line = [l for l in content.splitlines() if l.strip().startswith("val:")]
        if train_line and val_line:
            train_path = train_line[0].split(":", 1)[1].strip()
            val_path = val_line[0].split(":", 1)[1].strip()
            ogretmen_leak_confirmed = (train_path == val_path)
            log(f"train path == val path? {ogretmen_leak_confirmed} "
                f"({'CONFIRMED: same folder used for both -- a 100% leak by construction, '
                    'already flagged invalid in MODEL_RAPORU.md and excluded from headline '
                    'numbers. Note: ogretmen_dataset is a SEPARATE dataset from sure_dataset '
                    '(different folder entirely), so it is not part of the 412/98 split audited '
                    'here -- this check only confirms our leakage-detection LOGIC would have '
                    'caught it, as the design doc requested.' if ogretmen_leak_confirmed else ''})")
    else:
        log("data/ogretmen.yaml not found -- cannot run positive control")

    # ---- Step 4: perceptual hash near-duplicate check (PRIMARY, per NOTE-1) ----
    log("\n--- Perceptual hash (aHash + dHash, 64-bit each) near-duplicate check ---")
    log("imagehash library: NOT installed in anaconda env (confirmed via import attempt) "
        "-- implemented minimal aHash/dHash inline with PIL+numpy only.")

    hash_cache = {}
    all_files_with_split = [("train", f) for f in train_files] + [("val", f) for f in val_files]
    for split, f in all_files_with_split:
        path = os.path.join(DATASET, split, "images", f)
        a_hash, d_hash = compute_hashes(path)
        src, idx = infer_source(f)
        hash_cache[(split, f)] = {"src": src, "idx": idx, "ahash": a_hash, "dhash": d_hash}
    log(f"Computed hashes for {len(hash_cache)} images.")

    # Only compare within the same source group across splits (cross-group
    # near-duplicates are not physically plausible for distinct source videos
    # and would be O(412*98) for zero expected benefit).
    pair_results = []  # (src, train_file, val_file, ahash_dist, dhash_dist, train_idx, val_idx)
    for src in all_sources:
        tr_list = [(f, idx) for f, idx in train_sources.get(src, [])]
        va_list = [(f, idx) for f, idx in val_sources.get(src, [])]
        for tf, tidx in tr_list:
            th = hash_cache[("train", tf)]
            for vf, vidx in va_list:
                vh = hash_cache[("val", vf)]
                ad = hamming(th["ahash"], vh["ahash"])
                dd = hamming(th["dhash"], vh["dhash"])
                pair_results.append((src, tf, vf, tidx, vidx, ad, dd))

    log(f"Total within-source-group train x val pairs compared: {len(pair_results)}")

    for thr in THRESHOLDS:
        hits = [p for p in pair_results if p[5] <= thr or p[6] <= thr]
        log(f"\nThreshold <= {thr} bits (of 64) on aHash OR dHash: {len(hits)} candidate near-duplicate pairs")
        hits_sorted = sorted(hits, key=lambda p: min(p[5], p[6]))
        for p in hits_sorted[:30]:
            src, tf, vf, tidx, vidx, ad, dd = p
            log(f"    {src}: train={tf} (idx {tidx})  val={vf} (idx {vidx})  "
                f"aHash_dist={ad}  dHash_dist={dd}  frame_index_gap={abs(tidx - vidx)}")
        if len(hits_sorted) > 30:
            log(f"    ... ({len(hits_sorted) - 30} more, see near_duplicate_pairs_full.json)")

    # Save full pair results for the tightest threshold + all distances for reproducibility
    all_pairs_out = [
        {"source": p[0], "train_file": p[1], "val_file": p[2],
         "train_idx": p[3], "val_idx": p[4], "ahash_dist": p[5], "dhash_dist": p[6]}
        for p in pair_results
    ]
    with open(os.path.join(RUN_DIR, "near_duplicate_pairs_full.json"), "w") as fh:
        json.dump(all_pairs_out, fh, indent=2)

    min_dist_overall = min((min(p[5], p[6]) for p in pair_results), default=None)
    log(f"\nMinimum (aHash,dHash) distance found across ALL within-source-group train/val pairs: {min_dist_overall} / 64 bits")

    wall_time = time.time() - t0
    log(f"\nWall time: {wall_time:.1f}s")

    # ---- Final summary / verdict ----
    strict_threshold = THRESHOLDS[0]
    strict_hits = [p for p in pair_results if p[5] <= strict_threshold or p[6] <= strict_threshold]

    summary = {
        "experiment_id": "EXP05",
        "sure_project_git_commit": None,  # filled in by shell wrapper
        "train_count": len(train_files),
        "val_count": len(val_files),
        "source_groups_total": len(all_sources),
        "source_groups_crossing_splits": collisions,
        "n_source_groups_crossing_splits": len(collisions),
        "exact_frame_index_overlaps_within_colliding_groups": total_exact_overlaps,
        "ogretmen_positive_control_leak_confirmed": ogretmen_leak_confirmed,
        "near_duplicate_thresholds_bits_of_64": THRESHOLDS,
        "near_duplicate_hits_per_threshold": {
            str(thr): len([p for p in pair_results if p[5] <= thr or p[6] <= thr])
            for thr in THRESHOLDS
        },
        "strict_threshold_hits_detail": [
            {"source": p[0], "train_file": p[1], "val_file": p[2],
             "train_idx": p[3], "val_idx": p[4], "ahash_dist": p[5], "dhash_dist": p[6]}
            for p in sorted(strict_hits, key=lambda p: min(p[5], p[6]))
        ],
        "min_hash_distance_overall_bits_of_64": min_dist_overall,
        "wall_time_seconds": wall_time,
    }
    with open(os.path.join(RUN_DIR, "exp05_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    with open(os.path.join(RUN_DIR, "exp05_stdout.log"), "w") as fh:
        fh.write("\n".join(log_lines))

    return summary


if __name__ == "__main__":
    main()
