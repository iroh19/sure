"""
Retrain decision logic.

Kept separate from the Airflow DAG so the part that decides is testable without a
scheduler. `retrain_dag.py` is a thin wrapper that calls into here.

The pipeline is drift -> review -> retrain -> gate -> register, and the gate is
the point of it. Drift says the world changed; it does not say a new model would
be better. A retrain that ships automatically because a number crossed a line is
how a system quietly gets worse — the replacement has to beat the incumbent on
the same evaluation set before it is registered, and the comparison uses the
sure_v1 metrics already in the tracking store.

    python -m mlops.retrain --check recent.json      # what would happen
    python -m mlops.retrain --check recent.json --json out.json
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .drift import DriftReport, compare, load_reference

REPO = Path(__file__).resolve().parent.parent

# A retrained detector must clear the incumbent by more than run-to-run noise
# before it replaces it. Ultralytics training is not deterministic across runs;
# 0.005 mAP50 is comfortably above the wobble seen between epochs 62-79, which
# sat within ~0.002 of each other on the plateau.
MIN_IMPROVEMENT = 0.005

# Below this many detections the window is too thin to draw a distribution from,
# and PSI on a handful of points is noise. One hour of production at ~1 Hz with a
# typical 10-fish frame is far above this.
MIN_WINDOW = 200


@dataclass
class Decision:
    action: str            # "none" | "review" | "retrain"
    reason: str
    drift_psi: float | None = None
    drift_severity: str | None = None
    window_size: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


def decide(confidences: list[float], reference: list[float] | None = None) -> Decision:
    """What to do about a production window. Pure — no I/O, no training."""
    if len(confidences) < MIN_WINDOW:
        return Decision(
            action="none",
            reason=f"window too small ({len(confidences)} < {MIN_WINDOW} detections) "
                   f"to estimate a distribution",
            window_size=len(confidences),
        )

    reference = reference if reference is not None else load_reference()
    report: DriftReport = compare(reference, confidences)

    if report.severity == "significant":
        return Decision(
            action="retrain",
            reason=f"significant drift — {report.summary()}",
            drift_psi=report.psi,
            drift_severity=report.severity,
            window_size=len(confidences),
        )

    if report.severity == "moderate":
        return Decision(
            action="review",
            # Deliberately not a retrain. Moderate drift is common, and retraining
            # on every occurrence burns compute and risks replacing a good model
            # with a worse one fitted to a noisy window.
            reason="moderate drift — open a review, do not retrain automatically: "
                   + report.summary(),
            drift_psi=report.psi,
            drift_severity=report.severity,
            window_size=len(confidences),
        )

    return Decision(
        action="none",
        reason=f"no meaningful drift — {report.summary()}",
        drift_psi=report.psi,
        drift_severity=report.severity,
        window_size=len(confidences),
    )


def gate(candidate_map50: float, incumbent_map50: float) -> tuple[bool, str]:
    """Should the candidate replace the incumbent?

    Improvement has to exceed MIN_IMPROVEMENT, not merely be positive: training
    noise alone produces small positive deltas about half the time, and shipping
    on those is a coin flip dressed as a decision.
    """
    delta = candidate_map50 - incumbent_map50
    if delta > MIN_IMPROVEMENT:
        return True, (f"candidate mAP50 {candidate_map50:.4f} beats incumbent "
                      f"{incumbent_map50:.4f} by {delta:+.4f}")
    if delta > 0:
        return False, (f"candidate is better by only {delta:+.4f}, inside the "
                       f"{MIN_IMPROVEMENT} noise band — not shipping")
    return False, (f"candidate mAP50 {candidate_map50:.4f} does not beat incumbent "
                   f"{incumbent_map50:.4f} ({delta:+.4f})")


def incumbent_map50() -> float | None:
    """The shipped model's mAP50, from the tracking store."""
    try:
        from .tracking import EXPERIMENT, _mlflow

        mlflow = _mlflow()
        exp = mlflow.get_experiment_by_name(EXPERIMENT)
        if exp is None:
            return None
        runs = mlflow.search_runs(
            experiment_ids=[exp.experiment_id],
            filter_string="tags.metrics_valid = 'True'",
            order_by=["metrics.best_mAP50 DESC"],
            max_results=1,
        )
        if runs.empty:
            return None
        return float(runs.iloc[0]["metrics.best_mAP50"])
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Decide whether to retrain")
    ap.add_argument("--check", metavar="FILE", required=True,
                    help="JSON with a 'confidences' list from a production window")
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args()

    payload = json.loads(Path(args.check).read_text(encoding="utf-8"))
    decision = decide(payload["confidences"])

    print(f"action : {decision.action}")
    print(f"reason : {decision.reason}")

    if decision.action == "retrain":
        current = incumbent_map50()
        if current is None:
            print("\nNo incumbent in the tracking store — run "
                  "`python -m mlops.tracking --backfill` first.")
        else:
            print(f"\nIncumbent mAP50 {current:.4f}. A retrained model must exceed "
                  f"{current + MIN_IMPROVEMENT:.4f} to be registered.")

    if args.json:
        Path(args.json).write_text(json.dumps(decision.as_dict(), indent=1),
                                   encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
