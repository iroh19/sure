"""
EXP04 runner: re-run bench_agent's own measurement machinery (unmodified) for
ONE model against the original 5 scenarios + the 4 new scenarios (new_scenarios.py),
writing per-scenario results incrementally to a JSONL file (so a timeout/crash
partway through the (slow) AQUA-7B leg does not lose completed scenarios).

Usage: python run_bench.py <model_id> <output_stem>
  e.g. python run_bench.py KurmaAI/AQUA-1B aqua1b
       python run_bench.py KurmaAI/AQUA-7B aqua7b

Open decision resolved: AQUA_ADAPTER_PATH is left UNSET for this experiment.
bench_agent.py's own docstring frames this as measuring whether "a real model"
/ "the BASE model" can drive the closed-menu tool loop -- the README's
published 0%/0% and 60%/50% figures are reported with no "+adapter" framing
anywhere (unlike eval.py's decision-quality context, which explicitly is
"AQUA-1B + LoRA adapter"). No shell history, run log, or comment in the repo
was found indicating AQUA_ADAPTER_PATH was set for the original bench_agent.py
run. Matching that condition, this reproduction also leaves it unset.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.pop("AQUA_ADAPTER_PATH", None)  # explicit: unset, matching original condition

SURE_LLM_SERVICE = Path("/Users/batuhancitak/Desktop/sure-project/llm-service")
sys.path.insert(0, str(SURE_LLM_SERVICE))
sys.path.insert(0, str(Path(__file__).parent))

from agent.bench_agent import SCENARIOS as ORIGINAL_SCENARIOS, make_generator, run_once  # noqa: E402
from new_scenarios import NEW_SCENARIOS  # noqa: E402


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: python run_bench.py <model_id> <output_stem>")
        return 1
    model_id, stem = sys.argv[1], sys.argv[2]

    out_dir = Path(__file__).parent
    jsonl_path = out_dir / f"{stem}_results.jsonl"

    all_scenarios = list(ORIGINAL_SCENARIOS) + list(NEW_SCENARIOS)
    print(f"Model: {model_id}")
    print(f"AQUA_ADAPTER_PATH: {os.environ.get('AQUA_ADAPTER_PATH', '(unset)')}")
    print(f"Scenarios: {len(ORIGINAL_SCENARIOS)} original + {len(NEW_SCENARIOS)} new "
          f"= {len(all_scenarios)} total\n")

    t_load0 = time.time()
    generate = make_generator(model_id)
    print(f"[generator constructed in {time.time() - t_load0:.1f}s -- model itself "
          f"loads lazily on first _generate() call]\n")

    with open(jsonl_path, "w", encoding="utf-8") as fh:
        for i, sc in enumerate(all_scenarios, 1):
            origin = "original" if sc in ORIGINAL_SCENARIOS else "new"
            t0 = time.time()
            res = run_once(generate, sc)
            wall = time.time() - t0
            row = {
                "origin": origin,
                "scenario": res.scenario,
                "format_ok": res.format_ok,
                "first_tool": res.first_tool,
                "selection_ok": res.selection_ok,
                "steps": res.steps,
                "seconds": res.seconds,
                "wall_seconds": round(wall, 2),
                "stop_reason": res.stop_reason,
                "acceptable": sorted(sc.acceptable),
            }
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            fh.flush()
            mark = "-" if res.selection_ok is None else ("ok" if res.selection_ok else "XX")
            print(f"  [{i}/{len(all_scenarios)}] ({origin:8}) {mark:2} {res.scenario:32} "
                  f"format={'ok' if res.format_ok else 'XX':2} "
                  f"tool={str(res.first_tool):22} steps={res.steps} "
                  f"{res.seconds:5.1f}s  {res.stop_reason}")

    print(f"\nWritten: {jsonl_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
