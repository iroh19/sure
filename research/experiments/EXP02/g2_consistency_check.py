"""
EXP02 -- Eval-Harness / Production Rule-Path Consistency Audit.

Read-only against /Users/batuhancitak/Desktop/sure-project/. This script does
NOT modify the live repo; it only imports it (sys.path insertion) to prove
that llm-service/eval.py's rule_status() and backend/main.py's
rule_based_decision() ultimately call the exact same backend/rules.py
functions on the exact same 8 scenarios eval.py already ships.

Run with: /opt/anaconda3/bin/python3 g2_consistency_check.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SURE_ROOT = Path("/Users/batuhancitak/Desktop/sure-project")
BACKEND = SURE_ROOT / "backend"
LLM_SERVICE = SURE_ROOT / "llm-service"

# Make both backend/ and llm-service/ importable, backend first so that
# `import rules` resolves to backend/rules.py exactly as both main.py and
# eval.py do it themselves (path manipulation, not a copy).
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(LLM_SERVICE))

import rules  # noqa: E402  (backend/rules.py -- the single source)

# Import eval.py as a module without running its __main__ block, and without
# letting it try to import `inference` (which needs a loaded LLM). eval.py's
# module-level code only imports rules + argparse + defines SCENARIOS/funcs,
# so a plain import is safe and does not touch the LLM.
import importlib.util

eval_spec = importlib.util.spec_from_file_location("sure_eval", LLM_SERVICE / "eval.py")
sure_eval = importlib.util.module_from_spec(eval_spec)
eval_spec.loader.exec_module(sure_eval)  # noqa: this only defines functions/scenarios

# Import backend/main.py's VisionFrame/SensorReading/rule_based_decision.
# backend/main.py has heavier module-level side effects (FastAPI app, DB
# path resolution, background tasks) but none of them execute anything at
# import time beyond declarations and constant computation -- confirmed by
# reading the file: db_init()/app.run are only called under
# `if __name__ == "__main__"` / lifespan context, not at import time.
main_spec = importlib.util.spec_from_file_location("sure_backend_main", BACKEND / "main.py")
sure_main = importlib.util.module_from_spec(main_spec)
sys.modules["sure_backend_main"] = sure_main  # so pydantic can resolve forward refs via this module's globals
main_spec.loader.exec_module(sure_main)
sure_main.VisionFrame.model_rebuild()
sure_main.SensorReading.model_rebuild()


def git_provenance(path: Path) -> dict:
    head = subprocess.run(
        ["git", "-C", str(SURE_ROOT), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True
    ).stdout.strip()
    date = subprocess.run(
        ["git", "-C", str(SURE_ROOT), "log", "-1", "--format=%cI"],
        capture_output=True, text=True
    ).stdout.strip()
    return {"repo_head_short": head, "repo_head_date": date}


def main() -> int:
    results = []
    all_pass = True

    # --- Structural checks (import-path trace) ---
    structural = {
        "eval_py_imports_rules_via_syspath": sure_eval.rules is rules,
        "main_py_imports_same_rules_module_object": sure_main.rules is rules,
        "main_py_SEVERITY_is_rules_SEVERITY": sure_main.SEVERITY is rules.SEVERITY,
    }

    for sc in sure_eval.SCENARIOS:
        eval_status = sure_eval.rule_status(sc)

        vf = sure_main.VisionFrame(
            timestamp=datetime.now(timezone.utc).isoformat(),
            frame_id=0,
            fish_count=sc["vision"]["fish_count"],
            avg_activity=sc["vision"]["avg_activity"],
        )
        sr = sure_main.SensorReading(
            timestamp=datetime.now(timezone.utc).isoformat(),
            temperature_c=sc["sensor"]["temperature_c"],
            dissolved_oxygen_mgl=sc["sensor"]["dissolved_oxygen_mgl"],
            ph=sc["sensor"]["ph"],
            tds_ppm=sc["sensor"]["tds_ppm"],
        )
        backend_status = sure_main.rule_based_decision(vf, sr)["status"]

        agree = eval_status == backend_status
        all_pass = all_pass and agree
        results.append({
            "scenario_id": sc["id"],
            "name": sc["name"],
            "eval_py_rule_status": eval_status,
            "backend_main_rule_based_decision_status": backend_status,
            "agree": agree,
        })

    n_pass = sum(1 for r in results if r["agree"])
    report = {
        "experiment_id": "EXP02",
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_provenance": git_provenance(SURE_ROOT),
        "structural_checks": structural,
        "structural_checks_all_pass": all(structural.values()),
        "scenario_results": results,
        "scenario_agreement": f"{n_pass}/{len(results)}",
        "overall_pass": all_pass and all(structural.values()),
        "file_line_references": {
            "llm-service/eval.py": {
                "sys_path_insert_backend": "line 29 (`sys.path.insert(0, str(_BACKEND))`)",
                "import_rules": "line 31 (`import rules`)",
                "rule_status_fn": "line 95-97, calls `rules.evaluate_status(sc['sensor'], sc['vision'])`",
            },
            "backend/main.py": {
                "import_rules": "line 31 (`import rules`)",
                "SEVERITY_alias": "line 62 (`SEVERITY = rules.SEVERITY`)",
                "rule_based_decision_fn": "line 303-310, calls `rules.evaluate(...)`",
                "apply_rule_override_fn": "line 329-344, calls `rule_based_decision()` then compares "
                                           "`SEVERITY.get(rule['status'],0) > SEVERITY.get(parsed.get('status'),0)`",
            },
            "backend/rules.py": {
                "module_docstring": "lines 1-13, explicitly narrates the historical eval/production "
                                     "drift bug this experiment re-verifies is fixed",
                "SEVERITY_table": "line 32",
                "evaluate_fn": "line 50-88",
                "evaluate_status_fn": "line 91-93",
            },
        },
    }
    return report


if __name__ == "__main__":
    report = main()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if report["overall_pass"] else 1)
