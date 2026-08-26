"""
Can a local model drive the agent loop?

Tool calling is a trained capability and AQUA-1B's base (Gemma 3 1B) does not
have it. Saying "1B is too small" is easy; the engineering decision should rest
on a measurement — especially after the problem was deliberately shrunk from
free-form JSON generation to picking from a closed menu.

Measured separately:

  format     did a parseable `ARAC:` line come back? Without it the loop never
             starts.
  selection  was the first tool one of the reasonable ones for the scenario?

They are separate because they need different fixes: a model that cannot produce
the format needs prompting or constrained decoding, one that produces the format
and picks wrongly needs better tool descriptions.

    python -m agent.bench_agent
    python -m agent.bench_agent --model /path/to/local/mlx-model
    python -m agent.bench_agent --repeat 3
"""
from __future__ import annotations

import argparse
import os
import statistics
from dataclasses import dataclass

from .loop import PLAN_MAX_TOKENS, run_agent
from .tools import StaticDataSource


def _sensors(**overrides) -> list[dict]:
    base = {"temperature_c": 18.5, "dissolved_oxygen_mgl": 7.8, "ph": 7.1, "tds_ppm": 320.0}
    base.update(overrides)
    return [{"timestamp": f"t{i}", **base} for i in range(120)]


def _falling(param: str, start: float, end: float, n: int = 120) -> list[dict]:
    step = (end - start) / max(1, n - 1)
    rows = []
    for i in range(n):
        row = {"timestamp": f"t{i}", "temperature_c": 18.5,
               "dissolved_oxygen_mgl": 7.8, "ph": 7.1, "tds_ppm": 320.0}
        row[param] = start + step * i
        rows.append(row)
    return rows


def _vision(count: int = 6, act: float = 0.010) -> list[dict]:
    return [{"timestamp": f"t{i}", "frame_id": i, "fish_count": count, "avg_activity": act}
            for i in range(60)]


@dataclass
class Scenario:
    name: str
    snapshot: dict
    acceptable: set[str]     # empty = selection not scored
    source: StaticDataSource


SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name="oxygen falling",
        snapshot={"sensor": {"temperature_c": 19.0, "dissolved_oxygen_mgl": 5.4,
                             "ph": 7.1, "tds_ppm": 320.0},
                  "vision": {"fish_count": 6, "avg_activity": 0.009}},
        acceptable={"get_sensor_trend", "query_knowledge_base"},
        source=StaticDataSource(_falling("dissolved_oxygen_mgl", 7.9, 5.4), _vision()),
    ),
    Scenario(
        name="fish inactive, sensors normal",
        snapshot={"sensor": {"temperature_c": 18.5, "dissolved_oxygen_mgl": 7.8,
                             "ph": 7.1, "tds_ppm": 320.0},
                  "vision": {"fish_count": 6, "avg_activity": 0.0009}},
        acceptable={"get_fish_activity", "query_knowledge_base"},
        source=StaticDataSource(_sensors(), _vision(act=0.0009)),
    ),
    Scenario(
        name="no fish detected",
        snapshot={"sensor": {"temperature_c": 18.5, "dissolved_oxygen_mgl": 7.9,
                             "ph": 7.0, "tds_ppm": 315.0},
                  "vision": {"fish_count": 0, "avg_activity": 0.0}},
        acceptable={"get_fish_activity", "query_knowledge_base"},
        source=StaticDataSource(_sensors(), _vision(count=0, act=0.0)),
    ),
    Scenario(
        name="pH at the edge",
        snapshot={"sensor": {"temperature_c": 18.4, "dissolved_oxygen_mgl": 7.7,
                             "ph": 6.55, "tds_ppm": 300.0},
                  "vision": {"fish_count": 5, "avg_activity": 0.011}},
        acceptable={"get_sensor_trend", "query_knowledge_base"},
        source=StaticDataSource(_falling("ph", 7.2, 6.55), _vision()),
    ),
    Scenario(
        name="everything normal",
        # Calling no tool is correct here, and calling one is not wrong either.
        # This scenario checks restraint, not selection.
        snapshot={"sensor": {"temperature_c": 18.5, "dissolved_oxygen_mgl": 8.1,
                             "ph": 7.1, "tds_ppm": 320.0},
                  "vision": {"fish_count": 6, "avg_activity": 0.011}},
        acceptable=set(),
        source=StaticDataSource(_sensors(), _vision()),
    ),
)


def make_generator(model_id: str):
    """Borrow the production generation path.

    The measurement has to run the code that ships, or it measures something
    else — the same mistake `eval.py` once made with its copied rule logic.

    AQUA_BASE_MODEL must be set before the import; inference.py reads it at
    module level.
    """
    os.environ["AQUA_BASE_MODEL"] = model_id
    import inference

    def generate(prompt: str) -> str:
        # Planning is a choice, so sampling only adds noise. The token cap
        # matters: leaving the 512-token narration budget in place stretched a 7B
        # run from minutes to half an hour when the model missed its stop point.
        return inference._generate(prompt, temp=0.0, max_tokens=PLAN_MAX_TOKENS)

    return generate


@dataclass
class Result:
    scenario: str
    format_ok: bool
    first_tool: str | None
    selection_ok: bool | None
    steps: int
    seconds: float
    stop_reason: str


def run_once(generate, scenario: Scenario) -> Result:
    trace = run_agent(scenario.snapshot, scenario.source, generate)
    first = trace.tools_used[0] if trace.tools_used else None
    return Result(
        scenario=scenario.name,
        format_ok="biçimi tutturamadı" not in trace.stop_reason,
        first_tool=first,
        selection_ok=(first in scenario.acceptable) if scenario.acceptable else None,
        steps=trace.steps,
        seconds=trace.seconds,
        stop_reason=trace.stop_reason,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Measure whether a model can drive the agent loop")
    ap.add_argument("--model", default=os.getenv("AQUA_BASE_MODEL", "KurmaAI/AQUA-1B"))
    ap.add_argument("--repeat", type=int, default=1)
    args = ap.parse_args()

    print(f"Model: {args.model}   scenarios: {len(SCENARIOS)}   repeat: {args.repeat}\n")
    generate = make_generator(args.model)

    results: list[Result] = []
    for scenario in SCENARIOS:
        for _ in range(args.repeat):
            res = run_once(generate, scenario)
            results.append(res)
            mark = "-" if res.selection_ok is None else ("ok" if res.selection_ok else "XX")
            print(f"  {mark} {res.scenario:30} format={'ok' if res.format_ok else 'XX'} "
                  f"tool={str(res.first_tool):22} steps={res.steps} "
                  f"{res.seconds:5.1f}s  {res.stop_reason}")

    fmt = sum(r.format_ok for r in results) / len(results)
    scored = [r for r in results if r.selection_ok is not None]
    sel = (sum(r.selection_ok for r in scored) / len(scored)) if scored else float("nan")

    print("\n" + "-" * 76)
    print(f"Format compliance : {fmt:.0%}  ({sum(r.format_ok for r in results)}/{len(results)})")
    if scored:
        print(f"Tool selection    : {sel:.0%}  ({sum(r.selection_ok for r in scored)}/{len(scored)})")
    print(f"Mean steps        : {statistics.fmean(r.steps for r in results):.1f}")
    print(f"Mean duration     : {statistics.fmean(r.seconds for r in results):.1f}s")

    # Constant-answer detection. A model that picks the same tool everywhere is
    # not selecting; it is emitting a constant that happens to be right
    # sometimes. This is the most dangerous result to report naively, because
    # the number looks acceptable while the behaviour is broken.
    chosen = [r.first_tool for r in results if r.first_tool]
    constant = len(chosen) >= 3 and len(set(chosen)) == 1

    print()
    if constant:
        print(f"CONSTANT ANSWER: the model picked '{chosen[0]}' in all {len(chosen)} scenarios.")
        print("  It is not discriminating on input; the selection percentage above is")
        print("  incidental. This model cannot drive an LLM-planned agent loop.")
    elif fmt < 0.8:
        print("Format compliance is low — the model cannot even hold the closed-menu format.")
        print("  Options: a larger model, constrained decoding, or no agent path.")
    elif scored and sel < 0.6:
        print("Format is fine but selection is weak — the problem is tool discrimination,")
        print("  not prompt format. Sharpen the tool descriptions first.")
    else:
        print("This model can drive the loop.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
