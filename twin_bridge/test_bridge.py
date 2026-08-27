"""
Register decoding and the two-engine comparison, tested without a PLC.

The fake twin is the point: CODESYS and Godot are not available in CI, and a
comparison that can only be exercised by starting a soft PLC is a comparison
nobody runs.

    python -m pytest twin_bridge -v

Only needs pytest.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "backend"))

from twin_bridge.client import FakeTwin, TwinUnavailable  # noqa: E402
from twin_bridge.compare import compare_once, run  # noqa: E402
from twin_bridge.registers import (  # noqa: E402
    decode_alarms,
    decode_holding,
    decode_input,
    to_sure_snapshot,
)


def _holding(do=8.10, temp=18.5, ph=7.2, nh3=0.10, tds=320,
             appetite=55, stress=4, biomass=57, feed=0, auto=1):
    """Raw registers as Godot would write them, with the x100 scaling applied."""
    return [round(do * 100), round(temp * 100), round(ph * 100), round(nh3 * 100),
            round(tds), appetite, stress, biomass, feed, auto]


def _input(aerator=40, heater=0, feeder=0, portion=0, exchange=0,
           alarms=0, advice=0, feed_today=0):
    return [aerator, heater, feeder, portion, exchange, alarms, advice, feed_today]


# ── Scaling ──────────────────────────────────────────────────────────────────

def test_scaling_is_applied():
    """812 on the wire is 8.12 mg/L, not 812. Getting this wrong produces a
    plausible-looking number that is off by two orders of magnitude."""
    decoded = decode_holding(_holding(do=8.12, temp=19.4, ph=7.35, nh3=0.23))
    assert decoded["dissolved_oxygen_mgl"] == pytest.approx(8.12)
    assert decoded["temperature_c"] == pytest.approx(19.4)
    assert decoded["ph"] == pytest.approx(7.35)
    assert decoded["ammonia_mgl"] == pytest.approx(0.23)


def test_unscaled_registers_pass_through():
    decoded = decode_holding(_holding(tds=413, appetite=72, stress=18))
    assert decoded["tds_ppm"] == 413
    assert decoded["appetite_index"] == 72
    assert decoded["stress_index"] == 18


def test_short_frame_is_rejected():
    with pytest.raises(ValueError, match="expected 10"):
        decode_holding([0, 0, 0])


# ── Alarm bitfield ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("flags,expected", [
    (0b0000, []),
    (0b0001, ["dissolved oxygen low"]),
    (0b0010, ["ammonia high"]),
    (0b0101, ["dissolved oxygen low", "temperature out of band"]),
    (0b1111, ["dissolved oxygen low", "ammonia high",
              "temperature out of band", "stress high"]),
])
def test_alarm_bits_decode(flags, expected):
    assert decode_alarms(flags) == expected


def test_advice_code_is_translated():
    assert "amonyak" in decode_input(_input(alarms=0b0010, advice=2))["advice"]
    assert decode_input(_input(advice=99))["advice"] == "bilinmeyen kod"


# ── Snapshot shaping ─────────────────────────────────────────────────────────

def test_snapshot_carries_only_what_the_rule_engine_knows():
    snap = to_sure_snapshot(decode_holding(_holding()))
    assert set(snap["sensor"]) == {"temperature_c", "dissolved_oxygen_mgl",
                                   "ph", "tds_ppm"}
    assert "ammonia_mgl" not in snap["sensor"], (
        "adding a parameter here would put a threshold outside rules.py"
    )


def test_vision_channel_is_deliberately_empty():
    """The twin's appetite/stress are chemistry-derived and its fish do not move
    differently under stress. Mapping them onto S.U.R.E.'s movement-based channel
    would look like integration and measure nothing."""
    assert to_sure_snapshot(decode_holding(_holding(stress=90)))["vision"] is None


# ── Two-engine comparison ────────────────────────────────────────────────────

def test_both_engines_agree_when_oxygen_is_fine():
    status, alarms, kind, _ = compare_once(
        decode_holding(_holding(do=8.1)), decode_input(_input(alarms=0)))
    assert status == "ok" and kind == "agree" and alarms == []


def test_both_engines_agree_when_oxygen_is_low():
    status, _, kind, _ = compare_once(
        decode_holding(_holding(do=4.2)), decode_input(_input(alarms=0b0001)))
    assert status == "critical" and kind == "agree"


def test_ammonia_alarm_is_expected_divergence_not_a_bug():
    """S.U.R.E. has no ammonia sensor. That gap is stated, not silently ignored."""
    _, _, kind, note = compare_once(
        decode_holding(_holding(do=8.1, nh3=0.9)), decode_input(_input(alarms=0b0010)))
    assert kind == "expected"
    assert "ammonia sensor" in note


def test_real_disagreement_is_flagged_unexplained():
    """PLC sees low oxygen, S.U.R.E. does not — one of the two thresholds is wrong
    and this is the case worth arguing about."""
    _, _, kind, note = compare_once(
        decode_holding(_holding(do=8.0)), decode_input(_input(alarms=0b0001)))
    assert kind == "unexplained"
    assert "PLC says oxygen low" in note


def test_the_other_direction_is_also_flagged():
    _, _, kind, note = compare_once(
        decode_holding(_holding(do=4.0)), decode_input(_input(alarms=0)))
    assert kind == "unexplained"
    assert "S.U.R.E. says critical" in note


# ── Loop behaviour ───────────────────────────────────────────────────────────

def test_run_tallies_agreement_over_a_session():
    frames = [_holding(do=d) for d in (8.1, 7.9, 5.2, 4.4, 7.8)]
    alarms = [_input(alarms=a) for a in (0, 0, 0b0001, 0b0001, 0)]
    result = run(FakeTwin(frames, alarms), samples=5, interval=0, quiet=True)

    assert result.samples == 5
    assert result.agree == 5
    assert not result.unexplained


def test_run_stops_cleanly_when_the_twin_disappears():
    """A dropped PLC must end the session, not raise into the caller."""
    frames = [_holding()] * 5
    result = run(FakeTwin(frames, [_input()] * 5, fail_after=2),
                 samples=5, interval=0, quiet=True)
    assert result.samples == 2


def test_missing_twin_raises_a_readable_error():
    with pytest.raises(TwinUnavailable, match="no frames scripted"):
        FakeTwin().read()
