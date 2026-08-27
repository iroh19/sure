"""
EXP03 — Behavioral Four-Bucket Classification of AQUA-1B Through apply_rule_override.

Per experiment_design.json EXP03 and research_proposal.md's H1/H2 (Round-3,
four-bucket taxonomy): this script does what `llm-service/eval.py` never does
-- it pairs AQUA-1B's *actual* raw output with the *real* production safety
net, `backend.main.apply_rule_override()`, for each of eval.py's 8 SCENARIOS.

This is NOT a monkeypatch of eval.py or apply_rule_override -- it imports both
modules unmodified (sys.path insertion only, matching eval.py's own pattern)
and composes their public functions. GUARDRAIL: sure-project is read-only;
nothing under /Users/batuhancitak/Desktop/sure-project/ is written to.

Parseability instrumentation note (resolves an ambiguity in the written
procedure): the procedure's own hint for detecting the unparseable bucket
("reasoning field equal to raw[:500]") is a heuristic that can't be evaluated
from `generate_decision()`'s return value alone, since that function does not
expose whether its internal regex/json.loads succeeded -- only its final dict.
Rather than guess with a heuristic, this script reimplements
`generate_decision()`'s own parse logic, one level up, over the *same*
unmodified primitives it itself calls (`inference._decision_user_content`,
`inference._generate`) -- so we get a definitive parse_ok boolean instead of
inferring it. Exactly one `_generate()` call is made per scenario (same cost
as calling `generate_decision()` directly would be); the parsed-dict shape
produced here is byte-for-byte what `generate_decision()` would have returned
for the same raw text, so this is not a different code path, just an
instrumented composition of the same one.

Buckets (research_proposal.md Round 3, 4-bucket scheme):
  1. parseable-and-agrees                      -- model status == rule status
  2. parseable-and-under-calls-and-escalated    -- rule severity > model severity
                                                    (apply_rule_override.rule_override == True)
  3. parseable-and-over-calls                   -- model severity > rule severity
                                                    (apply_rule_override leaves this untouched --
                                                     it never downgrades, so this bucket is
                                                     only visible via a separate severity compare)
  4. unparseable-defaulted-to-ok                -- generate_decision's except-branch pathway fired
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

SURE_ROOT = Path("/Users/batuhancitak/Desktop/sure-project")
BACKEND_DIR = SURE_ROOT / "backend"
LLM_SERVICE_DIR = SURE_ROOT / "llm-service"

# Must be set BEFORE importing inference (module-level ADAPTER_PATH read at import time).
os.environ.setdefault("AQUA_ADAPTER_PATH", str(LLM_SERVICE_DIR / "sure-aqua-adapter"))

sys.path.insert(0, str(BACKEND_DIR))       # for `import rules`
sys.path.insert(0, str(LLM_SERVICE_DIR))   # for `import inference`

import rules  # noqa: E402
import inference  # noqa: E402

# Both `llm-service/main.py` and `backend/main.py` are top-level modules named
# `main` -- with both directories on sys.path, a plain `import main` would
# resolve to whichever directory sys.path happens to search first, silently
# picking the wrong one. Load backend/main.py by explicit file path under a
# distinct module name so there is no ambiguity about which "main" this is.
import importlib.util

_backend_main_spec = importlib.util.spec_from_file_location(
    "sure_backend_main", BACKEND_DIR / "main.py"
)
backend_main = importlib.util.module_from_spec(_backend_main_spec)
sys.modules["sure_backend_main"] = backend_main
_backend_main_spec.loader.exec_module(backend_main)

# eval.py is a script, not a package module; import it by file path to reuse
# its exact SCENARIOS list without redefining it (avoids drift between what
# this script tests and what eval.py tests).
_eval_spec = importlib.util.spec_from_file_location("sure_eval", LLM_SERVICE_DIR / "eval.py")
sure_eval = importlib.util.module_from_spec(_eval_spec)
_eval_spec.loader.exec_module(sure_eval)  # runs eval.py's module-level code (imports only, no I/O)

SEVERITY = rules.SEVERITY
OUT_DIR = Path(__file__).parent
RUN_LOG_PATH = OUT_DIR / "g3_run_log.jsonl"
RESULTS_JSON_PATH = OUT_DIR / "g3_results.json"


def build_vision_frame(sc: dict) -> backend_main.VisionFrame:
    """Per backend/test_decision.py's _vision() helper pattern."""
    v = sc["vision"]
    return backend_main.VisionFrame(
        timestamp="2026-08-26T00:00:00Z",
        frame_id=0,
        fish_count=v["fish_count"],
        avg_activity=v["avg_activity"],
        tracks=[],
    )


def build_sensor_reading(sc: dict) -> backend_main.SensorReading:
    """Per backend/test_decision.py's _sensor() helper pattern."""
    s = sc["sensor"]
    return backend_main.SensorReading(
        timestamp="2026-08-26T00:00:00Z",
        temperature_c=s["temperature_c"],
        dissolved_oxygen_mgl=s["dissolved_oxygen_mgl"],
        ph=s["ph"],
        tds_ppm=s["tds_ppm"],
    )


def instrumented_generate_decision(snapshot: dict) -> tuple[dict, bool, str]:
    """Reimplements inference.generate_decision()'s logic one level up so we
    get a definitive parse_ok flag, using the exact same unmodified
    primitives generate_decision() itself calls. Returns (parsed, parse_ok, raw)."""
    user_content, sources = inference._decision_user_content(snapshot)
    raw = inference._generate(user_content)
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise ValueError("no JSON object in model output")
        parsed = json.loads(m.group())
        parsed["engine"] = f"aqua-1b/{inference.BACKEND}"
        parsed["sources"] = sources
        return parsed, True, raw
    except (json.JSONDecodeError, AttributeError, ValueError):
        return (
            {
                "engine": f"aqua-1b/{inference.BACKEND}",
                "status": "ok",
                "reasoning": raw[:500],
                "recommendations": [],
                "sources": sources,
            },
            False,
            raw,
        )


def classify(parse_ok: bool, model_status_pre: str, rule_status: str,
             rule_override_fired: bool) -> str:
    if not parse_ok:
        return "unparseable-defaulted-to-ok"
    if model_status_pre == rule_status:
        return "parseable-and-agrees"
    if SEVERITY.get(rule_status, 0) > SEVERITY.get(model_status_pre, 0):
        return "parseable-and-under-calls-and-escalated"
    if SEVERITY.get(model_status_pre, 0) > SEVERITY.get(rule_status, 0):
        return "parseable-and-over-calls"
    return "other-unclassified"  # should not occur; SEVERITY is totally ordered over 3 values


def main() -> int:
    print("=" * 78)
    print("EXP03 -- Dual-Layer Behavioral Measurement (AQUA-1B x apply_rule_override)")
    print(f"AQUA_ADAPTER_PATH = {inference.ADAPTER_PATH!r} "
          f"(exists: {Path(inference.ADAPTER_PATH).exists() if inference.ADAPTER_PATH else False})")
    print(f"Backend = {inference.BACKEND}")
    print("=" * 78)

    # Adapter provenance
    adapter_path = Path(inference.ADAPTER_PATH)
    adapter_file = adapter_path / "adapters.safetensors"
    provenance = {
        "adapter_dir": str(adapter_path),
        "adapter_file_exists": adapter_file.exists(),
        "adapter_mtime": time.ctime(adapter_file.stat().st_mtime) if adapter_file.exists() else None,
        "git_tracked": False,  # confirmed via `git check-ignore` before this run:
        "note": (
            "llm-service/sure-aqua-adapter/ is gitignored (.gitignore line 58: "
            "'llm-service/sure-aqua-adapter*/'), so provenance is mtime-only, not a "
            "commit hash. `git log --all -- llm-service/sure-aqua-adapter` returns "
            "nothing. docker-compose.yml mounts sure-aqua-adapter (not test-adapter) "
            "at AQUA_ADAPTER_PATH=/adapter, confirming this is the deployed adapter. "
            "llm-service/test-adapter/adapters.safetensors (4.0MB) is not referenced "
            "anywhere in code/docs/compose and is excluded from this measurement; its "
            "provenance is unknown."
        ),
    }
    print(f"\nAdapter provenance: {json.dumps(provenance, indent=2)}\n")

    load_t0 = time.time()
    inference._load()
    load_s = time.time() - load_t0
    print(f"Model load time: {load_s:.1f}s\n")

    bucket_counts = {
        "parseable-and-agrees": 0,
        "parseable-and-under-calls-and-escalated": 0,
        "parseable-and-over-calls": 0,
        "unparseable-defaulted-to-ok": 0,
        "other-unclassified": 0,
    }
    rows = []
    run_log_fh = open(RUN_LOG_PATH, "w", encoding="utf-8")

    for sc in sure_eval.SCENARIOS:
        t0 = time.time()
        vision_obj = build_vision_frame(sc)
        sensor_obj = build_sensor_reading(sc)

        snapshot = {"sensor": sc["sensor"], "vision": sc["vision"], "safe_ranges": rules.SAFE}
        parsed, parse_ok, raw = instrumented_generate_decision(snapshot)
        model_status_pre = parsed.get("status", "?")

        rule = backend_main.rule_based_decision(vision_obj, sensor_obj)
        rule_status = rule["status"]

        # apply_rule_override mutates `parsed` in place and returns it.
        parsed_copy_for_override = dict(parsed)  # keep pre-override snapshot intact
        post = backend_main.apply_rule_override(parsed_copy_for_override, vision_obj, sensor_obj)
        rule_override_fired = bool(post.get("rule_override", False))
        post_status = post.get("status")

        bucket = classify(parse_ok, model_status_pre, rule_status, rule_override_fired)
        bucket_counts[bucket] += 1

        elapsed = time.time() - t0
        row = {
            "scenario_id": sc["id"],
            "scenario_name": sc["name"],
            "expected_eval_py": sc["expected"],
            "rule_status": rule_status,
            "model_status_pre_override": model_status_pre,
            "model_status_post_override": post_status,
            "rule_override_fired": rule_override_fired,
            "parse_ok": parse_ok,
            "bucket": bucket,
            "model_reasoning": parsed.get("reasoning", ""),
            "raw_model_output": raw,
            "elapsed_seconds": round(elapsed, 2),
        }
        rows.append(row)
        run_log_fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        run_log_fh.flush()

        print(f"[{sc['id']}] {sc['name']}")
        print(f"  rule_status={rule_status}  model_pre={model_status_pre}  "
              f"model_post={post_status}  rule_override={rule_override_fired}  "
              f"parse_ok={parse_ok}  bucket={bucket}  ({elapsed:.1f}s)")
        print(f"  reasoning: {row['model_reasoning'][:200]!r}")
        print()

    run_log_fh.close()

    print("=" * 78)
    print("BUCKET DISTRIBUTION (n=8):")
    for b, c in bucket_counts.items():
        if c > 0 or b != "other-unclassified":
            print(f"  {b:45s} {c}  ({c/8*100:.0f}%)")
    print("=" * 78)

    result = {
        "n_scenarios": len(sure_eval.SCENARIOS),
        "adapter_provenance": provenance,
        "model_load_seconds": round(load_s, 2),
        "bucket_counts": bucket_counts,
        "rows": rows,
    }
    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    print(f"\nFull results written: {RESULTS_JSON_PATH}")
    print(f"Per-scenario run log: {RUN_LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
