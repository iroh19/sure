"""
Airflow DAG: watch for drift, retrain only when it is warranted, ship only when
the result is better.

Deliberately thin. Everything that decides anything lives in `mlops/retrain.py`
and `mlops/drift.py`, which are plain functions with tests; this file is
scheduling and nothing else. A DAG that carries its own logic can only be tested
by running a scheduler, which is why so much orchestration code is untested.

    check_drift ──► decide ──┬─► (none)     stop
                             ├─► (review)   notify a human, stop
                             └─► (retrain)  retrain ─► evaluate ─► gate ─► register

The gate is the point. Drift means the world changed, not that a new model is
better; the candidate has to beat the incumbent on the same evaluation set by
more than training noise before it is registered.

Airflow is not a project dependency — this file is meant to be dropped into an
Airflow deployment's dags/ folder. It is not imported by any service and not
executed in CI.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import BranchPythonOperator, PythonOperator

REPO = Path(__file__).resolve().parent.parent
WINDOW_FILE = REPO / "mlops" / "recent_window.json"

DEFAULT_ARGS = {
    "owner": "sure",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


def _check_drift(**context):
    """Score the most recent production window."""
    import sys

    sys.path.insert(0, str(REPO))
    from mlops.retrain import decide

    payload = json.loads(WINDOW_FILE.read_text(encoding="utf-8"))
    decision = decide(payload["confidences"])
    context["ti"].xcom_push(key="decision", value=decision.as_dict())
    print(f"{decision.action}: {decision.reason}")
    return decision.action


def _branch(**context):
    action = context["ti"].xcom_pull(key="decision", task_ids="check_drift")["action"]
    return {"retrain": "retrain", "review": "notify_review"}.get(action, "stop")


def _retrain(**context):
    """Train a candidate. Left as the project's own training entry point rather
    than reimplemented here."""
    import subprocess
    import sys

    subprocess.run(
        [sys.executable, "train_sure.py"],
        cwd=REPO / "vision-service",
        check=True,
    )


def _evaluate_and_gate(**context):
    """Compare the candidate against the incumbent and decide whether it ships."""
    import sys

    sys.path.insert(0, str(REPO))
    from mlops.retrain import gate, incumbent_map50
    from mlops.tracking import best_epoch, read_results

    candidate_dir = REPO / "sure_models" / "sure_v1"
    rows = read_results(candidate_dir)
    if not rows:
        raise RuntimeError(f"no results.csv under {candidate_dir}")

    candidate = float(best_epoch(rows)["metrics/mAP50(B)"])
    incumbent = incumbent_map50()
    if incumbent is None:
        raise RuntimeError("no incumbent in the tracking store; run tracking --backfill")

    ok, reason = gate(candidate, incumbent)
    print(reason)
    context["ti"].xcom_push(key="ship", value=ok)
    if not ok:
        # Failing here is intentional: the run should be visibly red when a
        # retrain produced nothing worth shipping, not silently green.
        raise RuntimeError(f"candidate rejected — {reason}")


def _register(**context):
    import sys

    sys.path.insert(0, str(REPO))
    from mlops.tracking import RUNS, backfill, register

    run_dir, valid, caveat = RUNS["sure_v1"]
    run_id = backfill("sure_v1_retrain", run_dir, valid, caveat)
    if run_id:
        register(run_id)


def _notify_review(**context):
    decision = context["ti"].xcom_pull(key="decision", task_ids="check_drift")
    print(f"REVIEW NEEDED — {decision['reason']}")


def _stop(**context):
    print("no action")


with DAG(
    dag_id="sure_detector_retrain",
    description="Drift-triggered retraining for the S.U.R.E. detector",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="0 3 * * *",          # nightly, off-peak for the farm
    catchup=False,
    max_active_runs=1,             # never two retrains at once
    tags=["sure", "mlops"],
) as dag:

    check_drift = PythonOperator(task_id="check_drift", python_callable=_check_drift)
    branch = BranchPythonOperator(task_id="branch", python_callable=_branch)

    retrain = PythonOperator(task_id="retrain", python_callable=_retrain)
    evaluate = PythonOperator(task_id="evaluate_and_gate",
                              python_callable=_evaluate_and_gate)
    register_model = PythonOperator(task_id="register", python_callable=_register)

    notify_review = PythonOperator(task_id="notify_review",
                                   python_callable=_notify_review)
    stop = PythonOperator(task_id="stop", python_callable=_stop)

    check_drift >> branch
    branch >> retrain >> evaluate >> register_model
    branch >> notify_review
    branch >> stop
