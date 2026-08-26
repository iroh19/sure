"""
Deterministic evidence router.

Why this exists instead of an LLM-driven agent loop: `agent/bench_agent.py`
measured both local models against `agent/loop.py`. AQUA-1B never produced a
parseable action (0% format compliance); the 7B model produced the format 60% of
the time but selected `get_sensor_trend` in all five scenarios — a constant
answer, not a selection. Neither can drive the loop.

So the routing is code and the model only narrates. Tool definitions, validation
and execution are shared with `loop.py`; only the planner differs. If a
tool-capable model is introduced later, `loop.py` is already there and the
benchmark tells you whether it earns its place.

Evidence gathering never fails the decision. Any tool error becomes an
observation, and an unreachable backend yields no observations at all — the rule
engine still decides, the narration is just thinner.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from rag.thresholds import LABELS, load_activity_min, load_thresholds

from .tools import DataSource, ToolError, run_tool

# Cap on tool calls per decision. Each observation costs prompt budget, and a 1B
# model degrades with long context; four is already more than it can use.
MAX_CALLS = 4

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# What the model sees when a tool cannot run. Raw exception text would be noise
# it cannot act on; this states the fact in the language of the prompt. The real
# error goes to the log, not the context window.
_UNAVAILABLE = "(geçmiş veri şu anda okunamadı — trend bilgisi olmadan değerlendir)"


@dataclass
class Evidence:
    observations: list[tuple[str, str]] = field(default_factory=list)
    errors: int = 0

    def as_context(self, max_chars: int = 1600) -> str:
        out, used = [], 0
        for i, (tool, result) in enumerate(self.observations, 1):
            if used + len(result) > max_chars:
                break
            out.append(f"[G{i}] {result}")
            used += len(result)
        return "\n".join(out)


def plan(snapshot: dict) -> list[tuple[str, dict]]:
    """Pick tools from the snapshot. Pure function — no I/O, easy to test.

    This is a retrieval heuristic, not a safety decision: it only chooses what
    evidence to gather. `backend/rules.py` still owns the verdict. Thresholds
    come from the same single source the rule engine uses.
    """
    sensor = snapshot.get("sensor") or {}
    vision = snapshot.get("vision") or {}
    calls: list[tuple[str, dict]] = []
    deviations: list[str] = []

    for param, t in load_thresholds().items():
        value = sensor.get(param)
        if isinstance(value, (int, float)) and not (t.lo <= value <= t.hi):
            calls.append(("get_sensor_trend", {"parameter": param}))
            label = LABELS.get(param, (param, ""))[0]
            deviations.append(f"{label} {value} ({'düşük' if value < t.lo else 'yüksek'})")

    activity = vision.get("avg_activity")
    activity_min = load_activity_min()
    fish_count = vision.get("fish_count")
    behaviour_off = (
        (activity_min is not None and isinstance(activity, (int, float))
         and activity < activity_min)
        or fish_count == 0
    )
    if behaviour_off:
        calls.append(("get_fish_activity", {}))
        deviations.append(
            "hiç balık tespit edilmedi" if fish_count == 0 else "balık hareketliliği düşük"
        )

    # Sensor trends are the priority; the knowledge base fills the last slot so a
    # multi-parameter deviation does not crowd out the domain explanation.
    calls = calls[:MAX_CALLS - 1]
    query = (
        ", ".join(deviations) + " — neden olur, ne yapmalı"
        if deviations else "tüm parametreler normal, rutin refah takibi"
    )
    calls.append(("query_knowledge_base", {"query": query}))
    return calls


def gather(snapshot: dict, source: DataSource) -> Evidence:
    """Execute the planned tools and collect their output."""
    evidence = Evidence()
    for name, args in plan(snapshot):
        try:
            evidence.observations.append((name, run_tool(source, name, args)))
        except ToolError:
            evidence.errors += 1
            evidence.observations.append((name, _UNAVAILABLE))
    return evidence


def gather_with_sources(snapshot: dict, source: DataSource) -> tuple[Evidence, list[dict]]:
    """Same as `gather`, but keeps the knowledge-base hits structured.

    `query_knowledge_base` returns formatted text, which is what the model wants
    but loses the citation metadata the UI needs. Here the retrieval call is made
    directly so `[K1]` markers can be traced back to documents.
    """
    from rag.retriever import build_context, retrieve

    evidence = Evidence()
    sources: list[dict] = []

    for name, args in plan(snapshot):
        if name == "query_knowledge_base":
            context, sources = build_context(retrieve(args["query"]), max_chars=1200)
            if context:
                evidence.observations.append((name, context))
            continue
        try:
            evidence.observations.append((name, run_tool(source, name, args)))
        except ToolError:
            evidence.errors += 1
            evidence.observations.append((name, _UNAVAILABLE))

    return evidence, sources


def default_source() -> DataSource:
    """Read history from the backend.

    This makes llm-service call back into backend, which already called it. The
    two directions use different endpoints so nothing recurses, but it does
    couple the services. The alternative — backend shipping history inside the
    request — was rejected because it puts ~60 KB of raw readings on every
    decision call to save one local HTTP round trip.
    """
    from .tools import HttpDataSource

    return HttpDataSource(BACKEND_URL)
