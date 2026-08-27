#!/usr/bin/env python3
"""
EXP06 step 4 -- ONNX vs TorchScript per-image detection diff.

Goal: MODEL_RAPORU.md claims ONNX (cpu) and TorchScript (cpu) lose the exact
same -0.0104 mAP50 (and match to 4 decimals on mAP50-95: 0.5867 both) relative
to the pt/mps baseline, and attributes this to a SHARED POST-PROCESSING PATH
(NMS / decode) rather than independent numerical noise from two different
export toolchains. If that causal claim is right, the two formats should
produce near-identical per-image detections (same boxes surviving NMS), not
just the same aggregate mAP50 number by coincidence.

This script is read-only against sure-project: it loads the already-exported
best.onnx and best.torchscript artifacts under sure_models/sure_v1/export/
(produced earlier by vision-service/export_bench.py, not regenerated here)
and the 98 val images, and writes all output into this EXP06 run directory.

Method
------
For each of the 98 val images:
  1. Run YOLO(onnx_path).predict(img) and YOLO(torchscript_path).predict(img)
     with the SAME confidence/IoU thresholds (Ultralytics defaults: conf=0.25,
     iou=0.7 -- matches what model.val()/predict() uses unless overridden, so
     this is an apples-to-apples comparison at the deployed default operating
     point).
  2. Greedy IoU-matching (open_decision, resolved here): sort ONNX detections
     by confidence descending; for each, greedily claim the highest-IoU
     unclaimed TorchScript detection. Greedy (not Hungarian/optimal assignment)
     is used because at this detection density (median ~15 boxes/image, all
     the same class) a greedy confidence-first match is what a downstream
     "did these two exports agree" check would actually care about, and is
     far simpler to audit by hand than a Hungarian solver; the difference
     between greedy and optimal assignment is only material when boxes are
     nearly tied in IoU against multiple candidates, which we did not observe
     to be a large fraction of cases (see results.md for the count of images
     where greedy vs. optimal could plausibly differ, if any is flagged).
  3. IoU threshold for "agreement" vs "divergence" on a matched pair (open
     decision, resolved here): 0.9 (very strict -- boxes must overlap almost
     exactly, not just pass a normal detection-match bar of 0.5). This directly
     answers "do the two exports draw the SAME box", not "do they detect
     roughly the same fish", which is the stronger claim needed to support a
     shared-post-processing-path story.
  4. A "meaningfully different" image is one where: the two exports produce a
     different detection COUNT, OR any matched pair has IoU < 0.9, OR any
     detection in one export has no counterpart in the other at all.

Run with: /opt/anaconda3/bin/python3 g6_onnx_torchscript_diff.py
"""
import json
import os
import time

import numpy as np

SURE_ROOT = "/Users/batuhancitak/Desktop/sure-project"
ONNX_PATH = os.path.join(SURE_ROOT, "sure_models/sure_v1/export/best.onnx")
TS_PATH = os.path.join(SURE_ROOT, "sure_models/sure_v1/export/best.torchscript")
VAL_IMAGES_DIR = os.path.join(SURE_ROOT, "data/sure_dataset/val/images")
RUN_DIR = os.path.dirname(os.path.abspath(__file__))

IOU_AGREEMENT_THRESHOLD = 0.9  # strict: "drew the same box", not just "found a fish nearby"
CONF = 0.25  # Ultralytics default, matches deployed val()/predict() default
IOU_NMS = 0.7  # Ultralytics default NMS IoU


def box_iou(box_a, box_b):
    """IoU between two [x1,y1,x2,y2] boxes."""
    xa1, ya1, xa2, ya2 = box_a
    xb1, yb1, xb2, yb2 = box_b
    ix1, iy1 = max(xa1, xb1), max(ya1, yb1)
    ix2, iy2 = min(xa2, xb2), min(ya2, yb2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, xa2 - xa1) * max(0.0, ya2 - ya1)
    area_b = max(0.0, xb2 - xb1) * max(0.0, yb2 - yb1)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def greedy_match(dets_a, dets_b):
    """dets_a/dets_b: list of (box_xyxy, conf). Returns list of (i, j, iou) matched
    pairs (i index into dets_a, j index into dets_b), plus unmatched indices."""
    order_a = sorted(range(len(dets_a)), key=lambda i: -dets_a[i][1])
    used_b = set()
    matches = []
    for i in order_a:
        box_a = dets_a[i][0]
        best_j, best_iou = None, 0.0
        for j, (box_b, _conf_b) in enumerate(dets_b):
            if j in used_b:
                continue
            iou = box_iou(box_a, box_b)
            if iou > best_iou:
                best_iou, best_j = iou, j
        if best_j is not None and best_iou > 0.0:
            matches.append((i, best_j, best_iou))
            used_b.add(best_j)
    matched_a = {m[0] for m in matches}
    matched_b = {m[1] for m in matches}
    unmatched_a = [i for i in range(len(dets_a)) if i not in matched_a]
    unmatched_b = [j for j in range(len(dets_b)) if j not in matched_b]
    return matches, unmatched_a, unmatched_b


def main():
    t0 = time.time()
    from ultralytics import YOLO

    print(f"Loading ONNX model from {ONNX_PATH}")
    onnx_model = YOLO(ONNX_PATH)
    print(f"Loading TorchScript model from {TS_PATH}")
    ts_model = YOLO(TS_PATH)

    val_images = sorted(
        f for f in os.listdir(VAL_IMAGES_DIR) if f.lower().endswith((".jpg", ".jpeg", ".png"))
    )
    print(f"Val images: {len(val_images)}")

    per_image_results = []
    all_matched_ious = []
    n_images_meaningfully_different = 0
    n_images_same_count = 0
    n_images_diff_count = 0
    n_unmatched_dets_total = 0

    for fname in val_images:
        path = os.path.join(VAL_IMAGES_DIR, fname)
        r_onnx = onnx_model.predict(path, conf=CONF, iou=IOU_NMS, verbose=False, device="cpu")[0]
        r_ts = ts_model.predict(path, conf=CONF, iou=IOU_NMS, verbose=False, device="cpu")[0]

        onnx_boxes = r_onnx.boxes.xyxy.cpu().numpy() if r_onnx.boxes is not None else np.zeros((0, 4))
        onnx_confs = r_onnx.boxes.conf.cpu().numpy() if r_onnx.boxes is not None else np.zeros((0,))
        ts_boxes = r_ts.boxes.xyxy.cpu().numpy() if r_ts.boxes is not None else np.zeros((0, 4))
        ts_confs = r_ts.boxes.conf.cpu().numpy() if r_ts.boxes is not None else np.zeros((0,))

        dets_onnx = list(zip(onnx_boxes.tolist(), onnx_confs.tolist()))
        dets_ts = list(zip(ts_boxes.tolist(), ts_confs.tolist()))

        matches, unmatched_onnx, unmatched_ts = greedy_match(dets_onnx, dets_ts)
        ious = [m[2] for m in matches]
        all_matched_ious.extend(ious)

        same_count = len(dets_onnx) == len(dets_ts)
        n_images_same_count += int(same_count)
        n_images_diff_count += int(not same_count)
        n_unmatched_dets_total += len(unmatched_onnx) + len(unmatched_ts)

        low_iou_matches = [m for m in matches if m[2] < IOU_AGREEMENT_THRESHOLD]
        meaningfully_different = (
            not same_count or len(low_iou_matches) > 0 or unmatched_onnx or unmatched_ts
        )
        if meaningfully_different:
            n_images_meaningfully_different += 1

        per_image_results.append({
            "file": fname,
            "n_onnx_dets": len(dets_onnx),
            "n_ts_dets": len(dets_ts),
            "n_matched_pairs": len(matches),
            "median_matched_iou": float(np.median(ious)) if ious else None,
            "min_matched_iou": float(np.min(ious)) if ious else None,
            "n_low_iou_matches_below_0.9": len(low_iou_matches),
            "n_unmatched_onnx": len(unmatched_onnx),
            "n_unmatched_ts": len(unmatched_ts),
            "meaningfully_different": meaningfully_different,
        })

    wall_time = time.time() - t0

    all_ious_arr = np.array(all_matched_ious) if all_matched_ious else np.array([])
    summary = {
        "experiment_id": "EXP06",
        "sub_experiment": "onnx_vs_torchscript_per_image_diff",
        "iou_agreement_threshold": IOU_AGREEMENT_THRESHOLD,
        "matching_algorithm": "greedy (confidence-descending, highest-IoU unclaimed)",
        "conf_threshold_used": CONF,
        "nms_iou_used": IOU_NMS,
        "n_val_images": len(val_images),
        "n_images_meaningfully_different": n_images_meaningfully_different,
        "pct_images_meaningfully_different": round(
            100.0 * n_images_meaningfully_different / len(val_images), 1
        ),
        "n_images_same_detection_count": n_images_same_count,
        "n_images_different_detection_count": n_images_diff_count,
        "n_total_matched_pairs": len(all_matched_ious),
        "n_total_unmatched_detections": n_unmatched_dets_total,
        "matched_iou_median": float(np.median(all_ious_arr)) if len(all_ious_arr) else None,
        "matched_iou_mean": float(np.mean(all_ious_arr)) if len(all_ious_arr) else None,
        "matched_iou_min": float(np.min(all_ious_arr)) if len(all_ious_arr) else None,
        "matched_iou_p05": float(np.percentile(all_ious_arr, 5)) if len(all_ious_arr) else None,
        "pct_matched_pairs_below_0.9_iou": round(
            100.0 * sum(1 for i in all_matched_ious if i < IOU_AGREEMENT_THRESHOLD)
            / len(all_matched_ious), 2
        ) if all_matched_ious else None,
        "wall_time_seconds": wall_time,
    }

    with open(os.path.join(RUN_DIR, "g6_onnx_ts_diff_per_image.json"), "w") as fh:
        json.dump(per_image_results, fh, indent=2)
    with open(os.path.join(RUN_DIR, "g6_onnx_ts_diff_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print(json.dumps(summary, indent=2))
    print(f"\nWall time: {wall_time:.1f}s")
    return summary


if __name__ == "__main__":
    main()
