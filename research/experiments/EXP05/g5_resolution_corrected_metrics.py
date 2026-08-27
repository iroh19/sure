"""
G5 open-item resolution (results-formalization pass, post-verification).

verify_completion.json marked G5 "partial" because EXP05 enumerated the 32 near-duplicate
train/val pairs (14 adjacent-frame-index) but never produced a corrected/caveated headline
vision number. This script closes that gap via option (a) of the formalization brief:
recompute mAP50/precision/recall on best.pt after excluding the flagged val images, using
`model.val()` against a filtered copy of the val split (symlinked, not a modification of
sure-project's data/sure_dataset/ in place).

Inputs (read-only):
  - exp05_summary.json's strict_threshold_hits_detail (32 pairs, <=5-bit aHash/dHash distance)
  - sure_models/sure_v1/weights/best.pt (the same checkpoint EXP06/EXP07 measured)
  - data/sure_dataset/val/{images,labels} (98-image val split)

Two exclusion sets are exercised:
  1. The 14 adjacent-frame-index pairs (|train_idx - val_idx| == 1) -> 13 distinct val images
     excluded (one val file appears in 2 of the 14 pairs) -> 85-image val set.
  2. All 32 strict-threshold near-duplicate pairs -> 17 distinct val images excluded ->
     81-image val set (a more conservative / lower bound).

Output: precision/recall/mAP50/mAP50-95 on each filtered set vs. the unfiltered 98-image
baseline, run in the same session for an apples-to-apples comparison.

Run from sure-project root with: /opt/anaconda3/bin/python3 g5_resolution_corrected_metrics.py
(paths below assume that cwd; adjust SURE_ROOT if run elsewhere).
"""
import json
import os

from ultralytics import YOLO

SURE_ROOT = "/Users/batuhancitak/Desktop/sure-project"
EXP05_SUMMARY = os.path.join(
    "/Users/batuhancitak/Desktop/Experiments/PoggioAI-results/project_000",
    "experiment_workspace/experiment_runs/EXP05/exp05_summary.json",
)
SCRATCH_ROOT = "/tmp/g5_resolution_filtered_val"  # any writable scratch dir; not inside sure-project


def build_filtered_split(exclude_files, out_dir):
    img_dir = os.path.join(SURE_ROOT, "data/sure_dataset/val/images")
    lbl_dir = os.path.join(SURE_ROOT, "data/sure_dataset/val/labels")
    os.makedirs(os.path.join(out_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "labels"), exist_ok=True)
    kept = 0
    for fn in sorted(os.listdir(img_dir)):
        if not fn.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        if fn in exclude_files:
            continue
        kept += 1
        dst_img = os.path.join(out_dir, "images", fn)
        if not os.path.exists(dst_img):
            os.symlink(os.path.join(img_dir, fn), dst_img)
        base = os.path.splitext(fn)[0]
        src_lbl = os.path.join(lbl_dir, base + ".txt")
        dst_lbl = os.path.join(out_dir, "labels", base + ".txt")
        if os.path.exists(src_lbl) and not os.path.exists(dst_lbl):
            os.symlink(src_lbl, dst_lbl)
    yaml_path = out_dir + ".yaml"
    with open(yaml_path, "w") as f:
        f.write(
            f"path: {out_dir}\ntrain: train/images\nval: images\nnc: 1\nnames:\n  0: sturgeon\n"
        )
    os.symlink(
        os.path.join(SURE_ROOT, "data/sure_dataset/train"),
        os.path.join(out_dir, "train"),
    )
    return yaml_path, kept


def main():
    hits = json.load(open(EXP05_SUMMARY))["strict_threshold_hits_detail"]
    adjacent = [h for h in hits if abs(h["train_idx"] - h["val_idx"]) == 1]
    exclude_14pairs = sorted({h["val_file"] for h in adjacent})
    exclude_32pairs = sorted({h["val_file"] for h in hits})
    print(f"14 adjacent-index pairs -> {len(exclude_14pairs)} distinct val files excluded")
    print(f"32 strict-threshold pairs -> {len(exclude_32pairs)} distinct val files excluded")

    weights = os.path.join(SURE_ROOT, "sure_models/sure_v1/weights/best.pt")
    full_yaml = os.path.join(SURE_ROOT, "data/sure_dataset.yaml")

    results = {}
    m0 = YOLO(weights).val(data=full_yaml, verbose=False)
    results["baseline_98"] = {
        "precision": float(m0.box.mp), "recall": float(m0.box.mr),
        "map50": float(m0.box.map50), "map50_95": float(m0.box.map), "n_images": 98,
    }

    y14, n14 = build_filtered_split(set(exclude_14pairs), os.path.join(SCRATCH_ROOT, "excl14"))
    m1 = YOLO(weights).val(data=y14, verbose=False)
    results["excl_14_adjacent_pairs_13_files"] = {
        "precision": float(m1.box.mp), "recall": float(m1.box.mr),
        "map50": float(m1.box.map50), "map50_95": float(m1.box.map), "n_images": n14,
    }

    y32, n32 = build_filtered_split(set(exclude_32pairs), os.path.join(SCRATCH_ROOT, "excl32"))
    m2 = YOLO(weights).val(data=y32, verbose=False)
    results["excl_all_32_pairs_17_files"] = {
        "precision": float(m2.box.mp), "recall": float(m2.box.mr),
        "map50": float(m2.box.map50), "map50_95": float(m2.box.map), "n_images": n32,
    }

    print(json.dumps(results, indent=2))
    with open("g5_resolution_corrected_metrics_full.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
