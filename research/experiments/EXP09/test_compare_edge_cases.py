"""
EXP09 -- new FakeTwin-scripted edge-case tests for twin_bridge/compare.py.

This is a NEW test file living in experiment_workspace (NOT inside the live
sure-project repo, and NOT an edit to twin_bridge/test_bridge.py) per the
orchestrator's guardrail: sure-project is read-only reference material. It
imports twin_bridge/backend/rules.py from the live repo via sys.path
insertion, exactly the way twin_bridge/test_bridge.py itself does, and
otherwise touches nothing on disk in sure-project.

Targets three genuinely under-covered branches of compare_once() /
Comparison, identified by direct reading of twin_bridge/compare.py:

1. Multiple simultaneous EXPECTED_DIVERGENCE causes firing together (existing
   test_ammonia_alarm_is_expected_divergence_not_a_bug only exercises ONE
   expected cause at a time).
2. The "unmapped alarm string while do_low == sure_critical" branch inside
   compare_once (compare.py lines ~94-100: `if do_low == sure_critical: ...
   unexplained = [a for a in others if a not in EXPECTED_DIVERGENCE]`) --
   decode_alarms() can never itself produce a string outside the 4 fixed
   ALARM_BITS entries, so this branch is unreachable via any real Modbus
   frame or via FakeTwin.read() (which always routes through decode_input).
   compare_once(), however, accepts any raw `inputs` dict with an `alarms`
   key -- so a test can call compare_once() directly with a hand-built dict
   containing a string never seen in ALARM_BITS/EXPECTED_DIVERGENCE, reaching
   the branch without needing a live PLC or a change to registers.py's fixed
   4-bit vocabulary.
3. A single run() session scripting a mix of all three kinds (agree,
   expected, unexplained) together -- the existing
   test_run_tallies_agreement_over_a_session only scripts agree-vs-agree
   frames (5x agree), and test_run_stops_cleanly_when_the_twin_disappears
   only checks early termination, not kind-tallying. Neither confirms the
   Comparison aggregate counters correctly separate all three kinds within
   one session.

Run with:
  /opt/anaconda3/bin/python3 -m pytest \
    "/Users/batuhancitak/Desktop/Experiments/PoggioAI-results/project_000/experiment_workspace/experiment_runs/EXP09/test_compare_edge_cases.py" -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SURE_ROOT = Path("/Users/batuhancitak/Desktop/sure-project")
sys.path.insert(0, str(SURE_ROOT))
sys.path.insert(0, str(SURE_ROOT / "backend"))

from twin_bridge.client import FakeTwin  # noqa: E402
from twin_bridge.compare import EXPECTED_DIVERGENCE, compare_once, run  # noqa: E402
from twin_bridge.registers import decode_holding, decode_input  # noqa: E402


def _holding(do=8.10, temp=18.5, ph=7.2, nh3=0.10, tds=320,
             appetite=55, stress=4, biomass=57, feed=0, auto=1):
    """Same helper shape as twin_bridge/test_bridge.py's own _holding(), kept
    local so this file has no import-time dependency on test_bridge.py."""
    return [int(do * 100), int(temp * 100), int(ph * 100), int(nh3 * 100),
            int(tds), appetite, stress, biomass, feed, auto]


def _input(aerator=40, heater=0, feeder=0, portion=0, exchange=0,
           alarms=0, advice=0, feed_today=0):
    return [aerator, heater, feeder, portion, exchange, alarms, advice, feed_today]


# ── Edge case (a): multiple simultaneous expected-divergence causes ─────────

def test_multiple_simultaneous_expected_divergences_are_all_named():
    """ammonia high + temperature out of band + stress high fire together
    (alarms=0b1110, bits 1,2,3 -- NOT bit 0/dissolved-oxygen-low), with DO
    fine and S.U.R.E. status 'ok'. All three are named EXPECTED_DIVERGENCE
    causes; compare_once must classify the sample as 'expected' (not
    'unexplained') and its note must mention all three reasons, not just the
    first one encountered.
    """
    status, alarms, kind, note = compare_once(
        decode_holding(_holding(do=8.1)),
        decode_input(_input(alarms=0b1110)),
    )
    assert status == "ok"
    assert set(alarms) == {"ammonia high", "temperature out of band", "stress high"}
    assert kind == "expected"
    for cause in ("ammonia high", "temperature out of band", "stress high"):
        assert EXPECTED_DIVERGENCE[cause] in note, (
            f"expected note to mention the reason for {cause!r}, got: {note!r}"
        )


# ── Edge case (b): unmapped alarm string while do_low == sure_critical ──────

def test_unmapped_alarm_alongside_matching_oxygen_status_is_unexplained():
    """Construct a raw `inputs` dict directly (bypassing decode_input, which
    a real PLC frame or FakeTwin.read() always goes through and which can
    never emit anything outside the 4 fixed ALARM_BITS strings). This is the
    only way to reach compare_once's 'unmapped alarm string while
    do_low == sure_critical' branch: DO is critical (do=4.0, matching
    S.U.R.E.'s own 'critical' verdict so do_low == sure_critical == True),
    and the PLC alarm list additionally contains a string that exists in
    neither ALARM_BITS nor EXPECTED_DIVERGENCE. This is a genuinely
    reachable-but-previously-untested code path per direct reading of
    compare.py, not a restatement of existing coverage: the existing
    unexplained-divergence tests (test_real_disagreement_is_flagged_unexplained,
    test_the_other_direction_is_also_flagged) only cover the do_low != sure_critical
    branches (lines ~105-113), never the do_low == sure_critical branch with an
    unmapped extra alarm (lines ~94-100).
    """
    holding = decode_holding(_holding(do=4.0))  # < SAFE lower bound (6.0) -> S.U.R.E. 'critical'
    raw_inputs = {"alarms": ["dissolved oxygen low", "some_new_sensor_fault"]}

    status, alarms, kind, note = compare_once(holding, raw_inputs)

    assert status == "critical"
    assert kind == "unexplained"
    assert "some_new_sensor_fault" in note, (
        f"expected the unmapped alarm to be named in the note, got: {note!r}"
    )


def test_unmapped_alarm_note_does_not_swallow_it_as_expected():
    """Sanity companion to the above: confirm the unmapped string is not
    accidentally present in EXPECTED_DIVERGENCE (which would make the above
    test pass for the wrong reason if compare.py's dict were ever extended).
    """
    assert "some_new_sensor_fault" not in EXPECTED_DIVERGENCE


# ── Edge case (c): a single run() session mixing all three kinds ────────────

def test_run_session_separates_agree_expected_and_unexplained_within_one_session():
    """Script a 5-frame session via FakeTwin containing all three kinds at
    once (not just agree-vs-agree, as the existing
    test_run_tallies_agreement_over_a_session does): agree, expected,
    unexplained (both directions), agree again -- and confirm the
    Comparison aggregate counters (agree/expected/len(unexplained)) add up
    to samples and correctly separate all three kinds, not just tally two
    of them.

    Frame-by-frame classification (all via the real decode_holding/
    decode_input path, i.e. FakeTwin.read(), not a hand-built dict):
      1. do=8.1,  alarms=0        -> agree      (both say ok/no-alarm)
      2. do=8.1,  alarms=0b0010   -> expected   (ammonia high, DO fine, both ok)
      3. do=8.0,  alarms=0b0001   -> unexplained (PLC says DO low, S.U.R.E. says ok;
                                       do=8.0 is inside SAFE's (6.0, 12.0) band)
      4. do=4.0,  alarms=0        -> unexplained (S.U.R.E. says critical, PLC raised nothing)
      5. do=4.2,  alarms=0b0001   -> agree      (both say critical / DO-low)
    """
    holding_frames = [
        _holding(do=8.1),
        _holding(do=8.1),
        _holding(do=8.0),
        _holding(do=4.0),
        _holding(do=4.2),
    ]
    input_frames = [
        _input(alarms=0),
        _input(alarms=0b0010),
        _input(alarms=0b0001),
        _input(alarms=0),
        _input(alarms=0b0001),
    ]

    result = run(FakeTwin(holding_frames, input_frames), samples=5, interval=0, quiet=True)

    assert result.samples == 5
    assert result.agree == 2, f"expected 2 agree, got {result.agree}"
    assert result.expected == 1, f"expected 1 expected-divergence, got {result.expected}"
    assert len(result.unexplained) == 2, (
        f"expected 2 unexplained, got {len(result.unexplained)}: {result.unexplained}"
    )
    # Every sample must land in exactly one bucket.
    assert result.agree + result.expected + len(result.unexplained) == result.samples

    # Both unexplained directions should be represented (PLC-says-low and
    # S.U.R.E.-says-critical), confirming the aggregate list is not just
    # counting one direction twice.
    notes = [d.note for d in result.unexplained]
    assert any("PLC says oxygen low" in n for n in notes)
    assert any("S.U.R.E. says critical" in n for n in notes)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
