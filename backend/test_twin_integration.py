"""
sensor_loop source dispatch and the /api/twin endpoint shape.

These exist because the integration itself is the point of this feature — a
bridge that connects but is never exercised is indistinguishable from one that
doesn't work. No live PLC or Godot here: twin_bridge.client.FakeTwin stands in,
the same fake the bridge's own test suite uses.

    cd backend && python -m pytest test_twin_integration.py -v

Only needs pytest.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import main as backend_main  # noqa: E402
from twin_bridge.client import FakeTwin  # noqa: E402
from twin_bridge.registers import to_sure_snapshot  # noqa: E402


def _holding(do=8.10, temp=18.5, ph=7.2, nh3=0.10, tds=320,
             appetite=55, stress=4, biomass=57, feed=0, auto=1):
    return [round(do * 100), round(temp * 100), round(ph * 100), round(nh3 * 100),
            round(tds), appetite, stress, biomass, feed, auto]


def _input(aerator=40, heater=0, feeder=0, portion=0, exchange=0,
           alarms=0, advice=0, feed_today=0):
    return [aerator, heater, feeder, portion, exchange, alarms, advice, feed_today]


# ── sensor_loop dispatch ──────────────────────────────────────────────────────

def test_default_source_is_csv():
    """The default must not silently start expecting a PLC that may not exist."""
    assert backend_main.SENSOR_SOURCE == "csv"


def test_sensor_source_env_var_is_read_lowercase(monkeypatch):
    monkeypatch.setattr(backend_main, "SENSOR_SOURCE", "TWIN".strip().lower())
    assert backend_main.SENSOR_SOURCE == "twin"


# ── /api/twin shape, against a fake ───────────────────────────────────────────

@pytest.fixture
def twin_snapshot():
    """One decoded frame, as twin_sensor_loop would store it in twin_state."""
    holding_raw = _holding(do=4.2)
    input_raw = _input(alarms=0b0001, advice=1, aerator=100)
    fake = FakeTwin([holding_raw], [input_raw])
    from twin_bridge.registers import decode_holding, decode_input
    holding, inputs = decode_holding(holding_raw), decode_input(input_raw)
    fake.close()
    return holding, inputs


def test_twin_endpoint_reports_disabled_when_source_is_csv(monkeypatch):
    monkeypatch.setattr(backend_main, "SENSOR_SOURCE", "csv")
    monkeypatch.setattr(backend_main, "twin_state",
                        {"connected": False, "plc": None, "raw": None, "error": None})

    import asyncio
    result = asyncio.run(backend_main.get_twin())
    assert result["enabled"] is False
    assert "SENSOR_SOURCE=twin" in result["hint"]


def test_twin_endpoint_reports_disconnected_state(monkeypatch):
    monkeypatch.setattr(backend_main, "SENSOR_SOURCE", "twin")
    monkeypatch.setattr(backend_main, "twin_state",
                        {"connected": False, "plc": None, "raw": None,
                         "error": "no Modbus server at 127.0.0.1:502"})

    import asyncio
    result = asyncio.run(backend_main.get_twin())
    assert result == {
        "enabled": True, "connected": False,
        "error": "no Modbus server at 127.0.0.1:502",
    }


def test_twin_endpoint_shape_when_connected(monkeypatch, twin_snapshot):
    holding, inputs = twin_snapshot
    monkeypatch.setattr(backend_main, "SENSOR_SOURCE", "twin")
    monkeypatch.setattr(backend_main, "twin_state", {
        "connected": True, "raw": holding, "plc": inputs, "error": None,
    })

    import asyncio
    result = asyncio.run(backend_main.get_twin())

    assert result["enabled"] and result["connected"]
    assert result["sure"]["status"] == "critical"        # DO 4.2 < 6.0
    assert result["plc"]["alarms"] == ["dissolved oxygen low"]
    assert result["plc"]["aerator_pct"] == 100
    assert result["comparison"]["verdict"] == "agree"
    assert set(result["plant"]) == {"ammonia_mgl", "biomass_kg",
                                    "appetite_index", "stress_index"}


def test_twin_endpoint_surfaces_a_real_disagreement(monkeypatch):
    """PLC alarms on low oxygen, S.U.R.E.'s own read of the same registers does
    not — the case the whole comparison exists to catch."""
    from twin_bridge.registers import decode_holding, decode_input

    holding = decode_holding(_holding(do=8.0))           # S.U.R.E.: ok
    inputs = decode_input(_input(alarms=0b0001))          # PLC: alarms anyway

    monkeypatch.setattr(backend_main, "SENSOR_SOURCE", "twin")
    monkeypatch.setattr(backend_main, "twin_state",
                        {"connected": True, "raw": holding, "plc": inputs, "error": None})

    import asyncio
    result = asyncio.run(backend_main.get_twin())
    assert result["comparison"]["verdict"] == "unexplained"
    assert "PLC says oxygen low" in result["comparison"]["note"]


# ── snapshot shaping used by the loop ────────────────────────────────────────

def test_loop_would_feed_the_rule_engine_correctly():
    """End to end at the data level: twin registers -> sensor snapshot ->
    rules.evaluate, without starting the asyncio loop itself."""
    from twin_bridge.registers import decode_holding

    snapshot = to_sure_snapshot(decode_holding(_holding(do=4.5, temp=19.0)))
    verdict = backend_main.rules.evaluate(snapshot["sensor"], snapshot["vision"])
    assert verdict["status"] == "critical"
