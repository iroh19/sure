# EXP02 — Eval-Harness / Production Rule-Path Consistency Audit

**Status:** success (strong success criteria met)
**Repo state measured against:** sure-project @ `3c1b9fa` (2026-08-26T08:57:33+03:00), clean except pre-existing untracked `research_task.md` and `twin_bridge/` (both read-only reference material, not touched by this experiment).

## What was checked

Static code trace + one executable verification script
(`g2_consistency_check.py`, read-only against sure-project via `sys.path`
insertion and `importlib`, no files in sure-project modified):

1. **Structural / import-path trace** (re-verified by direct inspection, matches experiment_design.json's citations exactly):
   - `llm-service/eval.py` line 29 inserts `backend/` onto `sys.path`; line 31 does `import rules` (not a local copy).
   - `eval.py`'s `rule_status()` (lines 95-97) calls `rules.evaluate_status(sc["sensor"], sc["vision"])`.
   - `backend/main.py` line 31 does `import rules` — the identical module object, confirmed at runtime with `sure_eval.rules is sure_main.rules is rules` → `True`.
   - `backend/main.py` line 62: `SEVERITY = rules.SEVERITY` — same dict object (`is` check passes).
   - `rule_based_decision()` (lines 303-310) calls `rules.evaluate(...)`.
   - `apply_rule_override()` (lines 329-344) calls `rule_based_decision()` internally, then compares `SEVERITY.get(rule["status"],0) > SEVERITY.get(parsed.get("status"),0)` using the same `SEVERITY` table.
   - `backend/rules.py`'s own module docstring (lines 1-13) narrates the historical drift bug (fish_count==0: copy said "warning", production said "ok") and states the file is now the single, framework-independent source shared by both processes.

2. **Executable 8/8 scenario-agreement check**: for each of `eval.py`'s 8 `SCENARIOS`, constructed `backend.main.VisionFrame`/`SensorReading` pydantic objects and compared `eval.py.rule_status(sc)` against `backend.main.rule_based_decision(vf, sr)["status"]`.

## Result

- All 3 structural checks: **pass** (`eval_py_imports_rules_via_syspath`, `main_py_imports_same_rules_module_object`, `main_py_SEVERITY_is_rules_SEVERITY` all `True`).
- Scenario agreement: **8/8** (T01-T08, see `exp02_output.json` for full per-scenario detail).
- `overall_pass: true`.

## Interpretation

Both `eval.py` and `backend/main.py` resolve to the *exact same Python module object* for `rules` (confirmed via `is` identity check, not just value equality) — this is a stronger claim than "outputs happen to match today." No re-implemented or copy-drifted rule logic was found anywhere in either path. The historical drift bug that motivates the paper's opening narrative (a copied rule engine disagreeing with production on `fish_count==0`) cannot recur through this specific mechanism, because there is structurally only one `rules.py` and both processes import it by path, not by value or copy.

## Open decisions resolved

- EXP02 had no `open_decisions` listed in experiment_design.json (empty list) — none to resolve.

## Honest caveats

- This audit only proves the two *rule-evaluation* paths are consistent. It does NOT itself test `apply_rule_override()`'s interaction with actual model output (that is EXP03's scope, not this one) — `apply_rule_override()`'s own internal call to `rule_based_decision()` was traced by inspection (line reference above) but not separately re-executed end-to-end with a live model decision in this experiment, since that is out of EXP02's scope per its own procedure spec.
- `backend/main.py` was imported via `importlib` outside of a running FastAPI process; this executes all module-level code (including the `SEVERITY = rules.SEVERITY` alias and class definitions) but does not start the app or touch the SQLite DB (those are gated behind `if __name__ == "__main__"` / FastAPI lifespan hooks, confirmed by inspection before running).
