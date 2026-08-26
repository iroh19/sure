"""
Experiment tracking and the model registry.

Model files were living in git and being told apart by filename. That works until
there are three of them and nobody remembers which produced the number in the
report — which already happened once here: the report claimed epoch 73 while the
saved weights were epoch 77, because Ultralytics selects `best.pt` by fitness
rather than by mAP50. A registry exists to make that class of question answerable
instead of archaeological.

`--backfill` reads `results.csv` from the completed sure_v1 training run and logs
it, so the tracking store holds the real history from the first command rather
than starting empty and only filling up on the next retrain.

MLflow is optional at import time: if it is not installed the module still loads
and the functions explain what is missing. Nothing in the decision path depends
on it.

    python -m mlops.tracking --backfill        # log the existing sure_v1 run
    python -m mlops.tracking --list            # what is in the store
    mlflow ui --backend-store-uri sqlite:///mlops/mlflow.db
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# SQLite rather than the file store: MLflow put the filesystem backend into
# maintenance mode and it now refuses to open. SQLite is also what the registry
# needs — model versions and stage transitions have no file-store implementation.
STORE = REPO / "mlops" / "mlflow.db"
ARTIFACTS = REPO / "mlops" / "artifacts"
EXPERIMENT = "sure-detector"

# `valid` marks whether a run's metrics mean anything. The teacher model was
# trained and validated on the same 20 frames, so its 0.925 mAP50 measures
# memorisation, not generalisation. It is logged anyway — a registry that only
# holds the good runs cannot answer "why did we not ship that one".
RUNS = {
    "sure_v1": (REPO / "sure_models" / "sure_v1", True, ""),
    "ogretmen": (REPO / "sure_models" / "ogretmen", False,
                 "train set == val set (20 frames); metrics reflect leakage, "
                 "used only to auto-label the sure_v1 training data"),
}

# Ultralytics picks best.pt by fitness, not by the headline metric. Recording the
# formula alongside the run is what makes "which epoch shipped?" answerable.
FITNESS = "0.1*mAP50 + 0.9*mAP50-95"


def _mlflow():
    try:
        import mlflow
    except ImportError:
        raise SystemExit(
            "mlflow is not installed.\n  pip install 'mlflow>=2.16'"
        ) from None
    STORE.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(f"sqlite:///{STORE}")
    if mlflow.get_experiment_by_name(EXPERIMENT) is None:
        mlflow.create_experiment(EXPERIMENT, artifact_location=f"file://{ARTIFACTS}")
    mlflow.set_experiment(EXPERIMENT)
    return mlflow


def read_results(run_dir: Path) -> list[dict]:
    csv_path = run_dir / "results.csv"
    if not csv_path.exists():
        return []
    with open(csv_path, encoding="utf-8") as fh:
        return [{k.strip(): v for k, v in row.items()} for row in csv.DictReader(fh)]


def fitness_of(row: dict) -> float:
    return 0.1 * float(row["metrics/mAP50(B)"]) + 0.9 * float(row["metrics/mAP50-95(B)"])


def best_epoch(rows: list[dict]) -> dict | None:
    """The epoch Ultralytics would have saved — by fitness, not by mAP50."""
    return max(rows, key=fitness_of) if rows else None


def read_args(run_dir: Path) -> dict:
    args_path = run_dir / "args.yaml"
    if not args_path.exists():
        return {}
    params = {}
    for line in args_path.read_text(encoding="utf-8").splitlines():
        if ":" not in line or line.strip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if key in {"epochs", "batch", "imgsz", "lr0", "optimizer", "model",
                   "data", "patience", "device", "seed"}:
            params[key] = value
    return params


def backfill(name: str, run_dir: Path, valid: bool = True, caveat: str = "") -> str | None:
    mlflow = _mlflow()

    rows = read_results(run_dir)
    if not rows:
        print(f"  {name}: no results.csv, skipped")
        return None

    best = best_epoch(rows)
    weights = run_dir / "weights" / "best.pt"

    with mlflow.start_run(run_name=name) as run:
        mlflow.set_tags({
            "source": "backfill",
            "selection_rule": FITNESS,
            "weights_present": str(weights.exists()),
            "metrics_valid": str(valid),
            "caveat": caveat or "none",
        })
        mlflow.log_params({**read_args(run_dir), "epochs_completed": len(rows)})

        # The whole curve, so the plateau and the selection are both visible.
        for row in rows:
            step = int(float(row["epoch"]))
            mlflow.log_metrics({
                "precision": float(row["metrics/precision(B)"]),
                "recall": float(row["metrics/recall(B)"]),
                "mAP50": float(row["metrics/mAP50(B)"]),
                "mAP50_95": float(row["metrics/mAP50-95(B)"]),
                "fitness": fitness_of(row),
            }, step=step)

        mlflow.log_metrics({
            "best_epoch": int(float(best["epoch"])),
            "best_precision": float(best["metrics/precision(B)"]),
            "best_recall": float(best["metrics/recall(B)"]),
            "best_mAP50": float(best["metrics/mAP50(B)"]),
            "best_mAP50_95": float(best["metrics/mAP50-95(B)"]),
        })

        flag = "" if valid else "   [metrics not valid: leakage]"
        print(f"  {name}: {len(rows)} epochs, best = epoch "
              f"{int(float(best['epoch']))} "
              f"(mAP50 {float(best['metrics/mAP50(B)']):.4f}, "
              f"P {float(best['metrics/precision(B)']):.4f}, "
              f"R {float(best['metrics/recall(B)']):.4f}){flag}")
        return run.info.run_id


def register(run_id: str, name: str = "sure-detector") -> None:
    """Promote a run's weights into the registry.

    Deliberately separate from logging. A run is a record of what happened; a
    registered version is a claim that it should ship, and the two should not be
    the same action.
    """
    mlflow = _mlflow()
    result = mlflow.register_model(f"runs:/{run_id}/weights", name)
    print(f"registered {name} version {result.version}")


def list_runs() -> None:
    mlflow = _mlflow()
    exp = mlflow.get_experiment_by_name(EXPERIMENT)
    if exp is None:
        print(f"No experiment '{EXPERIMENT}' yet. Run --backfill first.")
        return

    runs = mlflow.search_runs(experiment_ids=[exp.experiment_id])
    if runs.empty:
        print("No runs logged.")
        return

    cols = ["tags.mlflow.runName", "tags.metrics_valid", "metrics.best_epoch",
            "metrics.best_mAP50", "metrics.best_precision", "metrics.best_recall"]
    print(runs[[c for c in cols if c in runs.columns]].to_string(index=False))


def main() -> int:
    ap = argparse.ArgumentParser(description="Experiment tracking for the detector")
    ap.add_argument("--backfill", action="store_true",
                    help="log completed training runs from their results.csv")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--register", metavar="RUN_ID")
    args = ap.parse_args()

    if args.backfill:
        print(f"Backfilling into {STORE.relative_to(REPO)}")
        ids = {}
        for name, (run_dir, valid, caveat) in RUNS.items():
            if run_dir.is_dir():
                run_id = backfill(name, run_dir, valid, caveat)
                if run_id:
                    ids[name] = run_id
        (REPO / "mlops" / "last_backfill.json").write_text(
            json.dumps(ids, indent=1), encoding="utf-8")
        return 0

    if args.list:
        list_runs()
        return 0

    if args.register:
        register(args.register)
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
