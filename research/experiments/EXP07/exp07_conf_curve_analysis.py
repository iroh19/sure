#!/usr/bin/env python3
"""
EXP07 step 3 (refined) -- fine-grained confidence-threshold curve analysis.

Why this script exists: exp07_conf_sweep.py (run first) called `model.val(conf=X)`
for several X and found box.mp/box.mr IDENTICAL (0.859/0.719) for every conf in
{0.10, 0.15, 0.20, 0.25, 0.30}, only changing once conf exceeded ~0.34. This is
itself a real methodological finding worth documenting (see results.md) -- it
means Ultralytics' DetMetrics.box.mp/mr are an argmax-over-the-RETAINED-curve
figure, not "precision/recall measured after filtering to exactly conf=X": as
long as X is below the internal best-F1 confidence, the reported P/R does not
move, because the metric still finds and reports the same best-F1 point inside
the range you allowed through.

To get the actually-useful numbers -- "what precision/recall does the deployed
system get AT conf=0.20 specifically" and "where exactly is the true F1 peak"
-- this script reads Ultralytics' full per-confidence curve arrays directly
(box.p_curve / box.r_curve / box.f1_curve, each length 1000 over conf in
[0,1]) from a SINGLE val() call, which is both more precise and cheaper than
looping many val(conf=X) calls.

Run with: /opt/anaconda3/bin/python3 exp07_conf_curve_analysis.py
"""
import json
import os
import time

import numpy as np

SURE_ROOT = "/Users/batuhancitak/Desktop/sure-project"
WEIGHTS = os.path.join(SURE_ROOT, "sure_models/sure_v1/weights/best.pt")
DATA = os.path.join(SURE_ROOT, "data/sure_dataset.yaml")
RUN_DIR = os.path.dirname(os.path.abspath(__file__))

DEPLOYED_CONF = 0.20
POINTS_OF_INTEREST = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]


def main():
    t0 = time.time()
    from ultralytics import YOLO

    model = YOLO(WEIGHTS)
    r = model.val(data=DATA, device="mps", verbose=False, plots=False)

    p_curve = np.asarray(r.box.p_curve)[0]   # class 0 (single-class model)
    r_curve = np.asarray(r.box.r_curve)[0]
    f1_curve = np.asarray(r.box.f1_curve)[0]
    x = np.linspace(0, 1, len(f1_curve))

    def at_conf(c):
        idx = int(np.abs(x - c).argmin())
        return {"conf": float(x[idx]), "precision": float(p_curve[idx]),
                "recall": float(r_curve[idx]), "f1": float(f1_curve[idx])}

    headline = {"precision": float(r.box.mp), "recall": float(r.box.mr),
                "map50": float(r.box.map50)}
    headline_f1 = 2 * headline["precision"] * headline["recall"] / (
        headline["precision"] + headline["recall"])

    true_argmax_idx = int(f1_curve.argmax())
    true_argmax = {"conf": float(x[true_argmax_idx]), "precision": float(p_curve[true_argmax_idx]),
                   "recall": float(r_curve[true_argmax_idx]), "f1": float(f1_curve[true_argmax_idx])}

    deployed_point = at_conf(DEPLOYED_CONF)

    points = {str(c): at_conf(c) for c in POINTS_OF_INTEREST}

    print(f"Headline (MODEL_RAPORU.md-equivalent, box.mp/box.mr): "
          f"P={headline['precision']:.4f} R={headline['recall']:.4f} F1={headline_f1:.4f} "
          f"mAP50={headline['map50']:.4f}")
    print(f"\nTrue F1-argmax on fine-grained curve (1000 conf points): "
          f"conf={true_argmax['conf']:.4f} P={true_argmax['precision']:.4f} "
          f"R={true_argmax['recall']:.4f} F1={true_argmax['f1']:.4f}")
    print(f"  -> Delta vs headline F1: {true_argmax['f1'] - headline_f1:+.4f} "
          f"({'headline is effectively at the peak, within curve resolution' if abs(true_argmax['f1'] - headline_f1) < 0.002 else 'headline is measurably off the true peak'})")

    print(f"\nAt DEPLOYED conf={DEPLOYED_CONF} (vision-service/yolo_runner.py CONF_THRESH): "
          f"P={deployed_point['precision']:.4f} R={deployed_point['recall']:.4f} "
          f"F1={deployed_point['f1']:.4f}")
    print("  -> This is the ACTUAL production operating point, and it is NOT the same as the "
          "headline P/R: precision is much lower (production trades precision for recall, "
          "consistent with yolo_runner.py's own comment that CONF_THRESH was deliberately "
          "lowered from 0.30 to 0.20 to raise recall on crowded frames), and recall is in fact "
          "HIGHER than the headline 0.719 figure at this specific operating point.")

    print("\nCurve at points of interest:")
    for c in POINTS_OF_INTEREST:
        pt = points[str(c)]
        marker = "  <-- DEPLOYED" if abs(c - DEPLOYED_CONF) < 1e-9 else ""
        print(f"  conf={c:.2f}: P={pt['precision']:.4f} R={pt['recall']:.4f} F1={pt['f1']:.4f}{marker}")

    wall_time = time.time() - t0
    summary = {
        "experiment_id": "EXP07",
        "sub_experiment": "confidence_threshold_curve_analysis",
        "headline_box_mp_mr": headline,
        "headline_f1": headline_f1,
        "true_f1_argmax_on_fine_curve": true_argmax,
        "headline_vs_true_argmax_f1_delta": true_argmax["f1"] - headline_f1,
        "deployed_conf": DEPLOYED_CONF,
        "deployed_operating_point": deployed_point,
        "points_of_interest": points,
        "methodological_note": (
            "model.val(conf=X) for X below the internal best-F1 confidence does NOT change "
            "box.mp/box.mr -- those are already an argmax-over-the-retained-curve figure, not "
            "a measurement pinned to conf=X. Confirmed empirically in exp07_conf_sweep.py: "
            "box.mp/mr were identical (0.859/0.719) for conf in {0.10,...,0.30} and only moved "
            "once conf exceeded the internal argmax threshold (~0.34). Reading the fine-grained "
            "p_curve/r_curve/f1_curve arrays directly (this script) is the correct way to get "
            "precision/recall AT a specific confidence threshold."
        ),
        "wall_time_seconds": wall_time,
    }
    with open(os.path.join(RUN_DIR, "exp07_conf_curve_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print(f"\nWall time: {wall_time:.1f}s")
    return summary


if __name__ == "__main__":
    main()
