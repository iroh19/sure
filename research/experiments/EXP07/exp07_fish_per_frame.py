#!/usr/bin/env python3
"""
EXP07 step 1+2 -- Fish-per-frame distribution from val ground truth, plus a
direct empirical full-frame-miss check on the actual sparse (low-k) frames.

Read-only against sure-project. Writes into this EXP07 run directory only.

Step 1: parse data/sure_dataset/val/labels/*.txt (YOLO format, one row per
fish per image) to build the ground-truth fish-per-frame histogram.

Step 2: per open_decision #1 (resolved: direct empirical count is primary,
the per-instance-independence approximation is a secondary sanity-check,
exactly as the design doc recommended) --
  (a) compute the naive independence-approximation estimate:
      P(full-frame miss | k fish) ~= (1 - recall)^k, using recall=0.719
      (MODEL_RAPORU.md headline, stated explicitly as an approximation because
      detections are not truly independent per frame given shared lighting/
      occlusion/camera-angle conditions within one frame).
  (b) run best.pt inference (deployed conf threshold, CONF_THRESH=0.20 per
      vision-service/yolo_runner.py, confirmed by reading that file) on every
      val frame and directly count actual full-frame misses (fish present per
      ground truth, zero detections returned) broken down by ground-truth k.

Run with: /opt/anaconda3/bin/python3 exp07_fish_per_frame.py
"""
import json
import os
import time
from collections import Counter, defaultdict

SURE_ROOT = "/Users/batuhancitak/Desktop/sure-project"
VAL_LABELS = os.path.join(SURE_ROOT, "data/sure_dataset/val/labels")
VAL_IMAGES = os.path.join(SURE_ROOT, "data/sure_dataset/val/images")
WEIGHTS = os.path.join(SURE_ROOT, "sure_models/sure_v1/weights/best.pt")
RUN_DIR = os.path.dirname(os.path.abspath(__file__))

RECALL_HEADLINE = 0.719  # MODEL_RAPORU.md, epoch 77, corrected 2026-08-26
DEPLOYED_CONF_THRESH = 0.20  # vision-service/yolo_runner.py line 44, confirmed by direct read


def load_gt_counts():
    """Return {filename_stem: fish_count} from YOLO-format label files.
    A label file with 0 rows (or missing) means 0 ground-truth fish in that frame."""
    counts = {}
    image_stems = sorted(
        os.path.splitext(f)[0] for f in os.listdir(VAL_IMAGES)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )
    for stem in image_stems:
        label_path = os.path.join(VAL_LABELS, stem + ".txt")
        if os.path.exists(label_path):
            with open(label_path) as fh:
                n = sum(1 for line in fh if line.strip())
        else:
            n = 0
        counts[stem] = n
    return counts


def main():
    t0 = time.time()
    gt_counts = load_gt_counts()
    n_images = len(gt_counts)
    total_fish = sum(gt_counts.values())
    print(f"Val images: {n_images}, total ground-truth fish: {total_fish}, "
          f"avg fish/frame: {total_fish / n_images:.2f}")
    print("(MODEL_RAPORU.md states 98 images / 1525 fish ~15.6/frame -- cross-check below)")

    hist = Counter(gt_counts.values())
    print("\nFish-per-frame histogram (k: n_frames):")
    for k in sorted(hist):
        print(f"  k={k:3d}: {hist[k]:3d} frames")

    # Naive independence approximation: P(miss | k) = (1 - recall)^k
    print("\n--- Independence-approximation full-frame-miss estimate (SECONDARY, per resolved open_decision) ---")
    approx_by_k = {}
    for k in sorted(hist):
        if k == 0:
            continue  # a 0-fish frame can't have a "miss" in this sense
        p_miss = (1 - RECALL_HEADLINE) ** k
        approx_by_k[k] = p_miss
        print(f"  k={k:3d}: P(full-frame miss) ~= (1-{RECALL_HEADLINE})^{k} = {p_miss:.5f}  "
              f"({hist[k]} frames at this k)")

    expected_misses_approx = sum(hist[k] * approx_by_k[k] for k in approx_by_k)
    print(f"\nExpected number of full-frame misses across val set (independence approx, "
          f"summed over frames with k>=1): {expected_misses_approx:.3f} out of "
          f"{sum(v for k, v in hist.items() if k >= 1)} frames with >=1 fish")

    # Low-k frames (k=1 or k=2) are where the approximation predicts the highest
    # per-frame miss probability -- these are exactly the frames to check empirically.
    low_k_stems = [stem for stem, k in gt_counts.items() if k in (1, 2)]
    print(f"\nLow-k (k=1 or k=2) frames to check empirically: {len(low_k_stems)}")

    # --- Step 2b: direct empirical check via best.pt inference ---
    print(f"\n--- Direct empirical full-frame-miss check (PRIMARY): "
          f"running best.pt at deployed conf={DEPLOYED_CONF_THRESH} on ALL val frames ---")
    from ultralytics import YOLO
    model = YOLO(WEIGHTS)

    empirical_misses = []  # list of (stem, k, n_detections)
    all_results = {}
    misses_by_k = defaultdict(int)
    frames_by_k = defaultdict(int)

    for stem, k in sorted(gt_counts.items()):
        if k == 0:
            continue  # ground-truth-empty frames excluded from "miss" definition
        img_path = os.path.join(VAL_IMAGES, stem + ".jpg")
        if not os.path.exists(img_path):
            # try other extensions
            for ext in (".jpeg", ".png"):
                if os.path.exists(os.path.join(VAL_IMAGES, stem + ext)):
                    img_path = os.path.join(VAL_IMAGES, stem + ext)
                    break
        r = model.predict(img_path, conf=DEPLOYED_CONF_THRESH, verbose=False, device="mps")[0]
        n_det = 0 if r.boxes is None else len(r.boxes)
        frames_by_k[k] += 1
        all_results[stem] = {"k_ground_truth": k, "n_detections": n_det}
        if n_det == 0:
            empirical_misses.append((stem, k, n_det))
            misses_by_k[k] += 1

    n_frames_with_fish = sum(v for k, v in gt_counts.items() if v is not None) - hist.get(0, 0)
    n_frames_with_fish = sum(1 for k in gt_counts.values() if k >= 1)
    n_empirical_misses = len(empirical_misses)
    print(f"\nFrames with >=1 ground-truth fish: {n_frames_with_fish}")
    print(f"Empirically observed full-frame misses (fish present, 0 detections at "
          f"conf={DEPLOYED_CONF_THRESH}): {n_empirical_misses} "
          f"({100.0 * n_empirical_misses / n_frames_with_fish:.2f}% of frames-with-fish)")
    print("\nEmpirical misses broken down by ground-truth k:")
    for k in sorted(frames_by_k):
        print(f"  k={k:3d}: {misses_by_k.get(k, 0)} / {frames_by_k[k]} frames missed entirely")
    if empirical_misses:
        print("\nDetail of missed frames:")
        for stem, k, n_det in empirical_misses:
            print(f"  {stem}: k_gt={k}, n_detections={n_det}")

    wall_time = time.time() - t0

    summary = {
        "experiment_id": "EXP07",
        "sub_experiment": "fish_per_frame_distribution_and_full_frame_miss",
        "n_val_images": n_images,
        "total_gt_fish": total_fish,
        "avg_fish_per_frame": round(total_fish / n_images, 3),
        "fish_per_frame_histogram": {str(k): v for k, v in sorted(hist.items())},
        "recall_headline_used_for_approx": RECALL_HEADLINE,
        "independence_approx_p_miss_by_k": {str(k): v for k, v in approx_by_k.items()},
        "independence_approx_expected_misses": expected_misses_approx,
        "deployed_conf_thresh_used_for_empirical_check": DEPLOYED_CONF_THRESH,
        "n_frames_with_ge1_fish": n_frames_with_fish,
        "n_empirical_full_frame_misses": n_empirical_misses,
        "pct_empirical_full_frame_misses": round(100.0 * n_empirical_misses / n_frames_with_fish, 3),
        "empirical_misses_by_k": {str(k): v for k, v in misses_by_k.items()},
        "empirical_miss_detail": [
            {"file": s, "k_ground_truth": k, "n_detections": n} for s, k, n in empirical_misses
        ],
        "wall_time_seconds": wall_time,
    }
    with open(os.path.join(RUN_DIR, "exp07_fish_per_frame_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    with open(os.path.join(RUN_DIR, "exp07_per_frame_detail.json"), "w") as fh:
        json.dump(all_results, fh, indent=2)

    print(f"\nWall time: {wall_time:.1f}s")
    return summary


if __name__ == "__main__":
    main()
