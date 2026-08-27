# EXP09 — twin_bridge Mechanism-Evidence Inventory + New FakeTwin Edge-Case Test

**Status:** success, with one honestly-reported pre-existing test failure in the live repo (not fixed — sure-project is read-only reference material per guardrails).
**Repo state:** sure-project @ `3c1b9fa`. Note: `twin_bridge/` is present on disk but shows as **untracked** in `git status` (`?? twin_bridge/`) — it has **zero git history** (`git log --oneline -- twin_bridge` returns nothing), unlike every other tracked module in the repo. This is itself a provenance finding, carried forward into EXP11.

Interpreter used: `/opt/anaconda3/bin/python3` (pytest 8.4.2), per the design pass's environment finding — the repo's own `./venv` lacks pytest.

## Step 1 — existing `test_bridge.py` suite

Ran: `/opt/anaconda3/bin/python3 -m pytest twin_bridge/test_bridge.py -v` from the sure-project root (read-only; no files modified). Full log: `existing_test_bridge_run.log`.

**Result: 18 passed, 1 failed** (19 collected, not "~18" as the design pass estimated — the parametrized `test_alarm_bits_decode` expands to 5 cases).

The one failure is real and reproducible, **not a flake**:

```
test_scaling_is_applied FAILED
  assert 8.11 == 8.12 ± 8.1e-06
  Obtained: 8.11
  Expected: 8.12
```

**Root cause (confirmed by direct inspection, not guessed):** `test_bridge.py`'s own `_holding()` test helper (line 36) builds raw register values with `int(do * 100)`. In IEEE-754 double precision, `8.12 * 100 == 811.9999999999999`, and Python's `int()` truncates toward zero rather than rounding, yielding `811` instead of `812`. `registers.py`'s actual production `Register.decode()` (`raw / self.scale`) then correctly returns `811 / 100 == 8.11`. **This is a bug in the test helper's float-to-int encoding, not in the production `decode()`/`decode_holding()` logic being tested** — the test asks for a value the helper cannot actually put on the wire given standard float rounding behavior. Verified interactively: `int(8.12*100) == 811`, `round(8.12*100) == 812`.

Per the guardrail treating sure-project as strictly read-only, this was **not fixed** — it is reported here exactly as found, with root cause identified via code reading rather than left as an unexplained red test.

## Step 2 — new FakeTwin-scripted edge-case tests

New file (NOT inside sure-project, NOT an edit to `test_bridge.py`): `test_compare_edge_cases.py`, imports `twin_bridge`/`backend.rules` from the live repo via `sys.path` insertion exactly as `test_bridge.py` itself does.

Four tests, all passing (`new_edge_case_test_run.log`):

1. **`test_multiple_simultaneous_expected_divergences_are_all_named`** — `alarms=0b1110` (ammonia + temperature + stress, DO fine) → confirms `kind=="expected"` and the note names all three `EXPECTED_DIVERGENCE` reasons, not just the first. Existing coverage (`test_ammonia_alarm_is_expected_divergence_not_a_bug`) only exercised one expected cause at a time.
2. **`test_unmapped_alarm_alongside_matching_oxygen_status_is_unexplained`** — the genuinely new target identified by direct reading of `compare.py` lines ~94-100: constructs a raw `inputs` dict directly (`{"alarms": ["dissolved oxygen low", "some_new_sensor_fault"]}`), bypassing `decode_input()` entirely (which can never itself emit a string outside `ALARM_BITS`'s 4 fixed entries). With DO critical (`do=4.0`, so `do_low == sure_critical == True`), confirms `compare_once()` correctly falls through to `kind=="unexplained"` with the unmapped alarm named in the note — a branch **structurally reachable but never exercised** by any existing test, since all of them go through `decode_input()` or hit the `do_low != sure_critical` branches instead (compare.py lines ~105-113).
3. **`test_unmapped_alarm_note_does_not_swallow_it_as_expected`** — companion sanity check that the injected string is genuinely absent from `EXPECTED_DIVERGENCE`.
4. **`test_run_session_separates_agree_expected_and_unexplained_within_one_session`** — a 5-frame `run()` session via `FakeTwin`, scripting agree → expected → unexplained (PLC-direction) → unexplained (S.U.R.E.-direction) → agree, in one session. Confirms `Comparison`'s aggregate counters (`agree=2`, `expected=1`, `len(unexplained)=2`, summing to `samples=5`) correctly separate all three kinds together, extending the existing `test_run_tallies_agreement_over_a_session` (which only scripted agree-vs-agree, 5x agree) and `test_run_stops_cleanly_when_the_twin_disappears` (which only checks early termination).

## Coverage inventory (before → after this experiment)

| category | before | after |
|---|---|---|
| agree (DO fine) | covered | covered |
| agree (DO critical) | covered | covered |
| expected divergence — single cause | covered (ammonia only) | covered |
| expected divergence — multiple simultaneous causes | **not covered** | **covered** (new test 1) |
| unexplained — PLC-low/SURE-not-critical | covered | covered |
| unexplained — SURE-critical/PLC-no-alarm | covered | covered |
| unexplained — unmapped alarm string, do_low==sure_critical branch | **not covered, and unreachable via any real PLC frame** | **covered via direct compare_once() call** (new test 2/3) |
| `run()` session mixing all 3 kinds together | **not covered** (only agree-only and early-termination sessions existed) | **covered** (new test 4) |

## Results 5.6 / Known Limitations #4 — required honest-status paragraph

> `twin_bridge`'s two-engine comparison mechanism (`backend/rules.py` vs. the twin's CODESYS logic) is **designed and unit-tested** (`twin_bridge/test_bridge.py`, 18/19 passing with one pre-existing float-rounding bug in a test helper documented above, plus 4 new FakeTwin-scripted edge-case tests added in this experiment, all passing) — it has **not** been exercised against a live twin session. No Godot/CODESYS installation, capture adapter, or live-session artifact was found anywhere in the repository during this pass, consistent with `research_plan.md`'s own "High likelihood" risk assessment that TB-3 (the live-session go/no-go checkpoint) would not materialize before freeze. All FakeTwin-scripted tests, existing and new, are **team-authored mechanism evidence** — the same team that wrote `compare.py` also wrote the frames that exercise it — and must never be described as, or conflated with, live cross-implementation corroboration against an independently-produced PLC/Godot session. The word "validated" is not used anywhere in connection with this mechanism absent an actual live run.

## Open decisions resolved

1. **"Has TB-3's live Godot/CODESYS checkpoint already resolved?"** — Resolved by direct filesystem check: no Godot installation, CODESYS project file, `plc/GVL_Godot.st` companion repo, or capture-adapter script exists anywhere under `/Users/batuhancitak/Desktop/sure-project/` (searched for `pymodbus`-dependent live-session artifacts and any `.st`/Godot project files; none found beyond the `twin_bridge/` package itself, which is designed to run standalone against `FakeTwin`). Confirms the "no-go" / not-yet-materialized status assumed in the design pass; this experiment's scope required no live-session upgrade.
2. **"Should further edge cases be added (e.g. a DO boundary case near the 6.0 mg/L threshold)?"** — Treated as optional per the open_decision's own framing ("a reasonable extension, not a required one") and not added, to keep this experiment's scope matched to its own success criteria (register-mismatch / within-tolerance / unexplained-divergence categories, all now covered). Flagged here as a legitimate future addition, not a gap in this experiment's completion.

## Additional provenance finding carried to EXP11

`twin_bridge/` is untracked in git (`git status` shows `?? twin_bridge/`; `git log -- twin_bridge` is empty) despite being fully present and functional on disk. Every number/claim in this results.md traces to the *file contents* at the time of this run (2026-08-26), not to a git commit hash, because none exists for this module yet.
