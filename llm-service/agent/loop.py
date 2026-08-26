"""
Hand-written agent loop.

    while step < budget:
        action = plan(state)        # LLM
        if no action: break
        result = run_tool(action)   # code
        state.observations += (action, result)

Everything else in this file is safety and recovery: a step budget, repetition
detection, tool errors fed back as observations, and a wall clock separate from
the step count (one hanging tool would otherwise never advance the counter).

Tool calling is a trained capability and neither local model has it, so the model
is not asked to generate a call — it picks from a closed menu and answers in two
lines. Parsing is lenient, validation is strict. If the format breaks twice the
loop finalises instead of locking up.

`generate` is injected, so the loop does not know which model it runs and can be
driven by a scripted fake in tests. `bench_agent.py` measures whether a real
model can drive it; as of the last run, neither can — see `router.py` for the
deterministic path that ships instead.

The safety net is unchanged: the agent only gathers evidence, the menu is
read-only, and `backend/rules.py` still decides.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable

from .tools import DataSource, ToolError, run_tool, tool_menu

# Evidence not gathered in four calls is not gathered in eight; the model just
# circles.
MAX_STEPS = 4
MAX_SECONDS = 45.0
PARSE_RETRIES = 1

# Planning answers are two lines, ~20 tokens. Sharing the 512-token narration
# budget stretched a 7B benchmark run from minutes to half an hour.
PLAN_MAX_TOKENS = 48


@dataclass
class Observation:
    tool: str
    args: dict
    result: str
    ok: bool = True


@dataclass
class AgentTrace:
    """Full record of a turn. Without it, agent debugging is guesswork."""
    observations: list[Observation] = field(default_factory=list)
    steps: int = 0
    stop_reason: str = ""
    parse_failures: int = 0
    seconds: float = 0.0

    @property
    def tools_used(self) -> list[str]:
        return [o.tool for o in self.observations]

    def as_context(self) -> str:
        if not self.observations:
            return ""
        return "\n".join(
            f"[Gözlem {i}] {o.tool}{'' if o.ok else ' (HATA)'}: {o.result}"
            for i, o in enumerate(self.observations, 1)
        )


_TOOL_RE = re.compile(r"ARAC\s*:\s*([a-z_]+)", re.IGNORECASE)
_ARGS_RE = re.compile(r"ARGS\s*:\s*(\{.*?\})", re.IGNORECASE | re.DOTALL)

# Small models paraphrase rather than repeat the instruction verbatim.
_DONE_WORDS = ("yok", "bitti", "yeter", "none", "hazir", "hazır")


def parse_action(raw: str) -> tuple[str | None, dict]:
    """Extract tool name and arguments.

    Lenient here (case, whitespace, surrounding chatter), strict in `run_tool`.
    The reverse — strict parsing, loose validation — produces both more failures
    and less safety.

    Returns (name | None, args); None means "stop and finalise".
    """
    m = _TOOL_RE.search(raw)
    if not m:
        return None, {}

    name = m.group(1).strip().lower()
    if name in _DONE_WORDS:
        return None, {}

    args: dict = {}
    a = _ARGS_RE.search(raw)
    if a:
        try:
            parsed = json.loads(a.group(1))
            if isinstance(parsed, dict):
                args = parsed
        except json.JSONDecodeError:
            # Name is readable, arguments are not: try the tool bare. If it has
            # required arguments, run_tool returns a message the model can act on.
            pass
    return name, args


def _plan_prompt(snapshot: dict, trace: AgentTrace, strict: bool = False) -> str:
    gozlemler = trace.as_context()
    gozlem_blok = f"\nŞUANA KADAR TOPLADIKLARIN:\n{gozlemler}\n" if gozlemler else ""

    biçim = (
        "SADECE şu iki satırı yaz, başka hiçbir şey yazma:\n"
        "ARAC: <araç_adı>\n"
        'ARGS: {"anahtar": "değer"}\n'
        if strict else
        "Bir araç çağırmak için:\n"
        "ARAC: <araç_adı>\n"
        'ARGS: {"anahtar": "değer"}\n\n'
        "Yeterince bilgi topladıysan:\n"
        "ARAC: yok\n"
    )

    return (
        "Bir su ürünleri tesisinde refah durumunu değerlendiriyorsun.\n"
        "Karar vermeden önce gerekirse araç çağırarak kanıt toplayabilirsin.\n\n"
        f"ARAÇLAR:\n{tool_menu()}\n"
        f"{gozlem_blok}\n"
        f"ANLIK VERİ:\n{json.dumps(snapshot, ensure_ascii=False)}\n\n"
        f"{biçim}"
    )


def run_agent(
    snapshot: dict,
    source: DataSource,
    generate: Callable[[str], str],
    max_steps: int = MAX_STEPS,
    max_seconds: float = MAX_SECONDS,
) -> AgentTrace:
    trace = AgentTrace()
    started = time.perf_counter()
    seen: set[tuple[str, str]] = set()

    while trace.steps < max_steps:
        if time.perf_counter() - started > max_seconds:
            trace.stop_reason = "zaman aşımı"
            break

        # `understood` separates a deliberate stop from a parse failure. Merging
        # them makes the trace lie: a model emitting garbage would be recorded as
        # having decided it had enough.
        name, args, understood = None, {}, False
        for attempt in range(PARSE_RETRIES + 1):
            raw = generate(_plan_prompt(snapshot, trace, strict=attempt > 0))
            name, args = parse_action(raw)
            if name is not None or "ARAC" in raw.upper():
                understood = True
                break
            trace.parse_failures += 1

        if not understood:
            trace.stop_reason = f"model {PARSE_RETRIES + 1} denemede de biçimi tutturamadı"
            break
        if name is None:
            trace.stop_reason = "model yeterli bilgi topladığını bildirdi"
            break

        # Same tool, same arguments: the model is stuck. No point burning budget.
        signature = (name, json.dumps(args, sort_keys=True, ensure_ascii=False))
        if signature in seen:
            trace.stop_reason = f"tekrar: {name} aynı argümanlarla yeniden istendi"
            break
        seen.add(signature)

        try:
            result = run_tool(source, name, args)
            trace.observations.append(Observation(name, args, result, ok=True))
        except ToolError as exc:
            # An error is an observation, not a crash — it gives the model a
            # chance to correct itself, which is the loop's main payoff.
            trace.observations.append(Observation(name, args, str(exc), ok=False))

        trace.steps += 1
    else:
        trace.stop_reason = f"adım bütçesi doldu ({max_steps})"

    trace.seconds = round(time.perf_counter() - started, 2)
    if not trace.stop_reason:
        trace.stop_reason = "tamamlandı"
    return trace
