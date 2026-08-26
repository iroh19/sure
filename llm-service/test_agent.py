"""
Agent tools and loop, tested without a model.

Agent debugging has two layers: did the model pick the wrong tool, or did the
tool misbehave? Keeping the tool layer green without a model eliminates the
second. A tool that needs a running backend or a loaded model is a tool nobody
tests.

    python -m pytest llm-service/test_agent.py -v

Only needs pytest.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent.tools import (  # noqa: E402
    TOOLS,
    StaticDataSource,
    ToolError,
    _direction,
    run_tool,
    tool_menu,
)


def _sensor_rows(values: list[float], key: str = "dissolved_oxygen_mgl") -> list[dict]:
    return [
        {
            "timestamp": f"2026-08-25T10:{i // 60:02d}:{i % 60:02d}Z",
            "temperature_c": 18.0,
            "dissolved_oxygen_mgl": 8.0,
            "ph": 7.0,
            "tds_ppm": 300.0,
            **{key: v},
        }
        for i, v in enumerate(values)
    ]


def _vision_rows(counts: list[int], acts: list[float]) -> list[dict]:
    return [
        {"timestamp": f"t{i}", "frame_id": i, "fish_count": c, "avg_activity": a}
        for i, (c, a) in enumerate(zip(counts, acts))
    ]


# ── Trend detection ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("values,expected", [
    ([8.0, 8.0, 8.0, 8.0, 8.0, 8.0], "sabit"),
    ([8.0, 7.5, 7.0, 6.5, 6.0, 5.5], "düşüyor"),
    ([5.5, 6.0, 6.5, 7.0, 7.5, 8.0], "yükseliyor"),
    ([8.0, 8.0], "belirsiz"),          # too few samples
])
def test_direction(values, expected):
    assert _direction(values) == expected


def test_direction_ignores_noise_without_trend():
    """Noise without direction reads as stable; without the band every wobble would be a trend."""
    assert _direction([7.0, 7.2, 6.9, 7.1, 7.0, 7.1, 6.95, 7.05]) == "sabit"


# ─── get_sensor_trend ─────────────────────────────────────────────────────────

def test_sensor_trend_summarises_instead_of_dumping():
    """200 rows must collapse to one sentence, not a data dump."""
    source = StaticDataSource(_sensor_rows([8.0 - i * 0.01 for i in range(200)]), [])
    out = run_tool(source, "get_sensor_trend", {"parameter": "dissolved_oxygen_mgl"})

    assert len(out) < 300, "tool output long enough to eat the context budget"
    assert "düşüyor" in out
    assert "çözünmüş oksijen" in out


def test_sensor_trend_reports_first_and_last():
    source = StaticDataSource(_sensor_rows([9.0, 8.0, 7.0, 6.0, 5.0, 4.0]), [])
    out = run_tool(source, "get_sensor_trend",
                   {"parameter": "dissolved_oxygen_mgl", "minutes": 5})
    assert "9.00" in out and "4.00" in out


def test_sensor_trend_handles_empty_history():
    """No data must not crash; return a sentence the model can use."""
    out = run_tool(StaticDataSource([], []), "get_sensor_trend", {"parameter": "ph"})
    assert "kayıt yok" in out


def test_sensor_trend_clamps_minutes():
    """An absurd window must clamp, not raise."""
    source = StaticDataSource(_sensor_rows([7.0] * 50), [])
    out = run_tool(source, "get_sensor_trend",
                   {"parameter": "ph", "minutes": 99999})
    assert "son 120 dakikada" in out


# ─── get_fish_activity ────────────────────────────────────────────────────────

def test_fish_activity_flags_zero_detection():
    """Zero detections must be surfaced: vision failure or serious stress."""
    source = StaticDataSource([], _vision_rows([5, 4, 0, 0, 3, 4], [0.01] * 6))
    out = run_tool(source, "get_fish_activity", {})
    assert "UYARI" in out and "hiç balık tespit edilmedi" in out


def test_fish_activity_without_vision_service():
    out = run_tool(StaticDataSource([], []), "get_fish_activity", {})
    assert "vision servisi bağlı olmayabilir" in out


# ── Nothing from the model is trusted ────────────────────────────────────────

def test_unknown_tool_is_rejected():
    with pytest.raises(ToolError, match="diye bir araç yok"):
        run_tool(StaticDataSource([], []), "drop_database", {})


def test_unknown_argument_is_rejected():
    """An invented argument must not be silently accepted."""
    with pytest.raises(ToolError, match="tanımsız argüman"):
        run_tool(StaticDataSource([], []), "get_fish_activity", {"tank_id": 3})


def test_missing_required_argument_is_rejected():
    with pytest.raises(ToolError, match="zorunlu argüman eksik"):
        run_tool(StaticDataSource([], []), "get_sensor_trend", {})


def test_invalid_enum_value_is_rejected():
    with pytest.raises(ToolError, match="geçerli bir parametre değil"):
        run_tool(StaticDataSource([], []), "get_sensor_trend",
                 {"parameter": "salinity"})


def test_tool_errors_are_readable_by_the_model():
    """The error is fed back to the model, so it must list valid options."""
    try:
        run_tool(StaticDataSource([], []), "get_sensor_trend", {"parameter": "xyz"})
    except ToolError as exc:
        assert "dissolved_oxygen_mgl" in str(exc), (
            "error must carry enough for the model to correct itself"
        )


# ── Menu ─────────────────────────────────────────────────────────────────────

def test_all_tools_are_read_only():
    """No write tools in the menu: decisions and alarms belong to the rule engine."""
    for name, tool in TOOLS.items():
        assert tool.read_only, f"{name} is a write tool and must not be in the menu"


def test_tool_menu_is_short_enough_for_a_1b_model():
    menu = tool_menu()
    assert len(menu) < 1200, "a longer menu costs a 1B model selection accuracy"
    for name in TOOLS:
        assert name in menu


def test_every_tool_has_a_model_facing_description():
    for name, tool in TOOLS.items():
        assert len(tool.description) > 40, (
            f"{name}: description too thin for the model to select on"
        )


# ── The loop, driven by a scripted model ─────────────────────────────────────
#
# `run_agent` takes `generate` as an argument, so "what does the loop do if the
# model says these things in this order" is answerable in milliseconds, without
# an LLM, and identically every run.
#
# Testing this against a real model would be slow, non-deterministic and would
# break whenever the model changed. Whether a real model can drive the loop is a
# measurement, not a test — see bench_agent.py.

from agent.loop import (  # noqa: E402
    AgentTrace,
    Observation,
    parse_action,
    run_agent,
)


class ScriptedModel:
    """Replays scripted responses, then reports done."""

    def __init__(self, *responses: str):
        self.responses = list(responses)
        self.calls: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.calls.append(prompt)
        if self.responses:
            return self.responses.pop(0)
        return "ARAC: yok"


def _source():
    return StaticDataSource(
        _sensor_rows([8.0 - i * 0.02 for i in range(120)]),
        _vision_rows([5] * 60, [0.01] * 60),
    )


# ── Parsing must be lenient ──────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected_tool", [
    ('ARAC: get_fish_activity\nARGS: {}', "get_fish_activity"),
    ('arac: get_fish_activity', "get_fish_activity"),                # küçük harf
    ('  ARAC :  get_fish_activity  ', "get_fish_activity"),          # boşluk
    ('Tabii, şunu yapayım.\nARAC: get_fish_activity\nARGS: {}', "get_fish_activity"),
    ('ARAC: yok', None),
    ('ARAC: bitti', None),
    ('tamamen alakasız metin', None),
])
def test_parse_action_is_lenient(raw, expected_tool):
    name, _ = parse_action(raw)
    assert name == expected_tool


def test_parse_action_extracts_args():
    name, args = parse_action(
        'ARAC: get_sensor_trend\nARGS: {"parameter": "ph", "minutes": 15}'
    )
    assert name == "get_sensor_trend"
    assert args == {"parameter": "ph", "minutes": 15}


def test_parse_action_survives_broken_json():
    """Broken arguments with a readable name should still attempt the tool."""
    name, args = parse_action('ARAC: get_fish_activity\nARGS: {bozuk json')
    assert name == "get_fish_activity"
    assert args == {}


# ── Loop behaviour ───────────────────────────────────────────────────────────

def test_loop_runs_tool_and_records_observation():
    model = ScriptedModel(
        'ARAC: get_sensor_trend\nARGS: {"parameter": "dissolved_oxygen_mgl"}',
        'ARAC: yok',
    )
    trace = run_agent({"sensor": {}}, _source(), model)

    assert trace.steps == 1
    assert trace.tools_used == ["get_sensor_trend"]
    assert trace.observations[0].ok
    assert "çözünmüş oksijen" in trace.observations[0].result
    assert trace.stop_reason == "model yeterli bilgi topladığını bildirdi"


def test_loop_stops_at_step_budget():
    """The budget must stop a model that keeps asking."""
    model = ScriptedModel(*[
        f'ARAC: get_sensor_trend\nARGS: {{"parameter": "ph", "minutes": {m}}}'
        for m in range(1, 20)
    ])
    trace = run_agent({"sensor": {}}, _source(), model, max_steps=3)

    assert trace.steps == 3
    assert "adım bütçesi doldu" in trace.stop_reason


def test_loop_detects_repetition():
    """Same tool and arguments means stuck; no need to burn the budget."""
    ayni = 'ARAC: get_fish_activity\nARGS: {}'
    trace = run_agent({"sensor": {}}, _source(), ScriptedModel(ayni, ayni, ayni))

    assert trace.steps == 1
    assert "tekrar" in trace.stop_reason


def test_repetition_check_allows_same_tool_with_different_args():
    """The same tool with different arguments is legitimate."""
    model = ScriptedModel(
        'ARAC: get_sensor_trend\nARGS: {"parameter": "ph"}',
        'ARAC: get_sensor_trend\nARGS: {"parameter": "tds_ppm"}',
        'ARAC: yok',
    )
    trace = run_agent({"sensor": {}}, _source(), model)
    assert trace.steps == 2


def test_tool_error_is_fed_back_not_raised():
    """A tool error becomes an observation, not a crash."""
    model = ScriptedModel(
        'ARAC: get_sensor_trend\nARGS: {"parameter": "salinity"}',   # geçersiz
        'ARAC: get_sensor_trend\nARGS: {"parameter": "ph"}',          # düzeltme
        'ARAC: yok',
    )
    trace = run_agent({"sensor": {}}, _source(), model)

    assert trace.steps == 2
    assert trace.observations[0].ok is False
    assert "geçerli bir parametre değil" in trace.observations[0].result
    assert trace.observations[1].ok is True


def test_model_can_self_correct_from_error_message():
    """The error must reach the observation context so the model can recover."""
    model = ScriptedModel(
        'ARAC: get_sensor_trend\nARGS: {"parameter": "salinity"}',
        'ARAC: yok',
    )
    trace = run_agent({"sensor": {}}, _source(), model)
    ctx = trace.as_context()
    assert "(HATA)" in ctx and "dissolved_oxygen_mgl" in ctx


def test_loop_reports_format_failure_honestly():
    """A format failure must not be reported as a deliberate stop."""
    model = ScriptedModel("bugün hava çok güzel", "yine alakasız bir cevap")
    trace = run_agent({"sensor": {}}, _source(), model)

    assert trace.steps == 0
    assert "biçimi tutturamadı" in trace.stop_reason
    assert trace.parse_failures >= 1


def test_loop_retries_once_with_strict_prompt():
    """A broken first answer earns one stricter retry."""
    model = ScriptedModel(
        "şöyle düşünüyorum ki",                        # bozuk
        'ARAC: get_fish_activity\nARGS: {}',           # düzeldi
        'ARAC: yok',
    )
    trace = run_agent({"sensor": {}}, _source(), model)

    assert trace.steps == 1
    assert trace.parse_failures == 1
    assert "SADECE şu iki satırı yaz" in model.calls[1], "second attempt must be strict"


def test_zero_step_run_is_still_valid():
    """An immediate stop yields an empty turn, which is not an error."""
    trace = run_agent({"sensor": {}}, _source(), ScriptedModel("ARAC: yok"))
    assert trace.steps == 0
    assert trace.observations == []
    assert trace.as_context() == ""


def test_trace_records_timing():
    trace = run_agent({"sensor": {}}, _source(), ScriptedModel("ARAC: yok"))
    assert trace.seconds >= 0.0


# ── Deterministic router ─────────────────────────────────────────────────────
#
# `plan` is pure, so tool selection is testable without a model or a database —
# which is the whole reason routing moved into code after the benchmark showed
# neither local model could select reliably.

from agent.router import MAX_CALLS, Evidence, gather, plan  # noqa: E402


def _snap(do=7.8, temp=18.5, ph=7.1, tds=320.0, count=6, act=0.010):
    return {
        "sensor": {"temperature_c": temp, "dissolved_oxygen_mgl": do,
                   "ph": ph, "tds_ppm": tds},
        "vision": {"fish_count": count, "avg_activity": act},
    }


def test_router_always_asks_the_knowledge_base():
    """Domain explanation is wanted in every case, deviation or not."""
    for snapshot in (_snap(), _snap(do=5.0)):
        assert plan(snapshot)[-1][0] == "query_knowledge_base"


def test_router_requests_trend_for_the_deviating_parameter():
    tools = plan(_snap(do=5.0))
    trend = [args for name, args in tools if name == "get_sensor_trend"]
    assert {"parameter": "dissolved_oxygen_mgl"} in trend


def test_router_ignores_parameters_within_range():
    tools = [name for name, _ in plan(_snap())]
    assert "get_sensor_trend" not in tools


def test_router_reacts_to_low_activity():
    assert "get_fish_activity" in [name for name, _ in plan(_snap(act=0.0001))]


def test_router_reacts_to_zero_fish():
    assert "get_fish_activity" in [name for name, _ in plan(_snap(count=0))]


def test_router_respects_the_call_budget():
    """Every parameter out of range must still fit the budget."""
    tools = plan(_snap(do=2.0, temp=30.0, ph=4.0, tds=900.0, count=0, act=0.0))
    assert len(tools) <= MAX_CALLS


def test_router_query_names_the_deviation():
    query = plan(_snap(do=5.0))[-1][1]["query"]
    assert "Oksijen" in query and "düşük" in query


def test_router_query_is_generic_when_nothing_deviates():
    assert "normal" in plan(_snap())[-1][1]["query"]


def test_gather_survives_a_missing_data_source():
    """An unreachable backend degrades the narration, never the decision."""

    class Broken:
        def sensor_history(self):
            raise ConnectionError("backend down")

        def vision_history(self):
            raise ConnectionError("backend down")

    evidence = gather(_snap(do=5.0), Broken())
    assert evidence.errors >= 1
    # The model gets a plain statement, not a Python traceback.
    assert any("okunamadı" in result for _, result in evidence.observations)
    assert not any("ConnectionError" in result for _, result in evidence.observations)


def test_evidence_context_respects_its_budget():
    evidence = Evidence(observations=[("t", "x" * 900), ("t", "y" * 900)])
    assert len(evidence.as_context(max_chars=1000)) < 1100
