#!/usr/bin/env python3
"""
EXP07 step 3 -- confidence-threshold precision/recall/F1 sweep on best.pt,
to confirm (or correct) whether P=0.858/R=0.719 (MODEL_RAPORU.md headline) is
the true F1-argmax operating point.

Read-only against sure-project. Writes into this EXP07 run directory only.

Open decision (which conf values to sweep), resolved: the design doc proposed
0.15/0.25/0.35 "around a typical Ultralytics default of 0.25" but flagged that
the actual deployed threshold in vision-service/yolo_runner.py was not
independently re-confirmed. Direct read of that file (line 44) found:
    CONF_THRESH = 0.20   # 0.30->0.20: yogun karelerde recall artisi (daha az kacan balik)
i.e. the deployed threshold is 0.20, not 0.25, and its own inline comment
records that it was deliberately lowered from 0.30 to 0.20 specifically to
raise recall on crowded frames -- a real prior tuning decision, not a default.
Given that, the sweep here is widened and centered around BOTH the deployed
0.20 and the Ultralytics-conventional 0.25, at a finer grid than the original
3-point proposal, to properly localize the F1-argmax: 0.10, 0.15, 0.20 (deployed),
0.25, 0.30, 0.35, 0.40.

Note on what "P=0.858/R=0.719" actually is: Ultralytics' `model.val()` with no
`conf` argument computes precision/recall/mAP by evaluating a full internal
confidence sweep, and DetMetrics.box.mp/mr report precision/recall AT THE
CONFIDENCE THAT MAXIMIZES PER-CLASS F1 across that internal curve -- this is
already an F1-argmax figure over an unconstrained sweep, not a measurement at
the deployed conf=0.20. This script's job is to check whether explicitly
constraining val() to a single fixed conf (as production inference effectively
does) ever BEATS that unconstrained-argmax headline number, and specifically
where the deployed conf=0.20 operating point falls on the curve.

Run with: /opt/anaconda3/bin/python3 exp07_conf_sweep.py
"""
import json
import os
import time

SURE_ROOT = "/Users/batuhancitak/Desktop/sure-project"
WEIGHTS = os.path.join(SURE_ROOT, "sure_models/sure_v1/weights/best.pt")
DATA = os.path.join(SURE_ROOT, "data/sure_dataset.yaml")
RUN_DIR = os.path.dirname(os.path.abspath(__file__))

DEPLOYED_CONF = 0.20
SWEEP_POINTS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]


def main():
    t0 = time.time()
    from ultralytics import YOLO

    # Unconstrained headline run (no conf arg -> Ultralytics' own internal
    # argmax-over-full-curve figure, i.e. reproduces MODEL_RAPORU.md's P/R).
    print("=== Unconstrained val() (Ultralytics internal F1-argmax over full curve) ===")
    model = YOLO(WEIGHTS)
    r_unconstrained = model.val(data=DATA, device="mps", verbose=False, plots=False)
    p_u = float(r_unconstrained.box.mp)
    r_u = float(r_unconstrained.box.mr)
    f1_u = 2 * p_u * r_u / (p_u + r_u) if (p_u + r_u) > 0 else 0.0
    print(f"Unconstrained: P={p_u:.4f} R={r_u:.4f} F1={f1_u:.4f} mAP50={float(r_unconstrained.box.map50):.4f}")

    print("\n=== Fixed-confidence sweep (val() constrained to a single conf threshold) ===")
    rows = []
    for conf in SWEEP_POINTS:
        model_i = YOLO(WEIGHTS)  # fresh instance per run to avoid any cached-state effects
        r = model_i.val(data=DATA, device="mps", conf=conf, verbose=False, plots=False)
        p = float(r.box.mp)
        rec = float(r.box.mr)
        f1 = 2 * p * rec / (p + rec) if (p + rec) > 0 else 0.0
        map50 = float(r.box.map50)
        marker = "  <-- DEPLOYED (yolo_runner.py CONF_THRESH)" if conf == DEPLOYED_CONF else ""
        print(f"conf={conf:.2f}: P={p:.4f} R={rec:.4f} F1={f1:.4f} mAP50={map50:.4f}{marker}")
        rows.append({"conf": conf, "precision": p, "recall": rec, "f1": f1, "map50": map50,
                     "is_deployed": conf == DEPLOYED_CONF})

    argmax_row = max(rows, key=lambda x: x["f1"])
    wall_time = time.time() - t0

    summary = {
        "experiment_id": "EXP07",
        "sub_experiment": "confidence_threshold_sweep",
        "deployed_conf_thresh": DEPLOYED_CONF,
        "unconstrained_val_result": {"precision": p_u, "recall": r_u, "f1": f1_u,
                                      "map50": float(r_unconstrained.box.map50)},
        "sweep_points": SWEEP_POINTS,
        "sweep_results": rows,
        "f1_argmax_among_swept_points": argmax_row,
        "is_unconstrained_headline_the_true_argmax": abs(f1_u - argmax_row["f1"]) < 1e-6 or f1_u >= argmax_row["f1"],
        "wall_time_seconds": wall_time,
    }
    with open(os.path.join(RUN_DIR, "exp07_conf_sweep_summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)

    print(f"\nF1-argmax among swept fixed-conf points: conf={argmax_row['conf']} "
          f"(F1={argmax_row['f1']:.4f}) vs. unconstrained headline F1={f1_u:.4f}")
    print(f"\nWall time: {wall_time:.1f}s")
    return summary


if __name__ == "__main__":
    main()
