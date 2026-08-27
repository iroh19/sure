"""
EXP04 — >=4 new, genuinely distinct Scenario entries for llm-service/agent/bench_agent.py.

Built with the exact same Scenario/StaticDataSource/_falling/_vision/_sensors
helper machinery bench_agent.py itself defines (imported unmodified, not
copied/reimplemented), following the style of the original 5. These are NEW
inputs (different sensor trajectories / vision fixtures), not repeats of the
same 5 cases and not `--repeat N` (which the original bench_agent.py runs at
temp=0.0, greedy, so repeats are byte-identical and add zero information --
confirmed directly in make_generator()'s `generate()`).

Each targets a distinct discrimination/robustness angle beyond the original 5:

  A. "temperature rising, DO fine"      -- rising (not falling) trend on a
                                           DIFFERENT parameter than the
                                           original "oxygen falling" case, to
                                           check the model isn't just pattern-
                                           matching "trend exists -> get_sensor_trend"
                                           regardless of which parameter/direction.
  B. "pH improving, not degrading"      -- current reading is borderline-low
                                           (like the original "pH at the edge")
                                           but the TREND is recovering upward,
                                           not falling toward the edge -- tests
                                           whether tool choice is driven by the
                                           current snapshot alone or genuinely
                                           informed by trend-seeking behaviour.
  C. "low activity + falling TDS"       -- combines two signal categories the
                                           original 5 only ever present alone
                                           (vision-only concern in "fish inactive",
                                           sensor-only concern in "oxygen falling"/
                                           "pH at the edge"): does the model
                                           reach for either evidence-gathering
                                           tool, or get confused by two
                                           simultaneous cues?
  D. "borderline but safe on all axes"  -- like "everything normal" (restraint
                                           test, empty acceptable set), but with
                                           every parameter close to (not far
                                           from) its safe-range edge, checking
                                           whether proximity-to-threshold alone
                                           triggers unnecessary tool calls.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path("/Users/batuhancitak/Desktop/sure-project/llm-service")))

from agent.bench_agent import Scenario, StaticDataSource, _falling, _sensors, _vision  # noqa: E402

NEW_SCENARIOS: tuple[Scenario, ...] = (
    Scenario(
        name="temperature rising (new-A)",
        snapshot={"sensor": {"temperature_c": 22.3, "dissolved_oxygen_mgl": 7.6,
                             "ph": 7.2, "tds_ppm": 310.0},
                  "vision": {"fish_count": 7, "avg_activity": 0.012}},
        acceptable={"get_sensor_trend", "query_knowledge_base"},
        source=StaticDataSource(_falling("temperature_c", 17.0, 22.3), _vision()),
    ),
    Scenario(
        name="pH improving (new-B)",
        snapshot={"sensor": {"temperature_c": 18.6, "dissolved_oxygen_mgl": 7.9,
                             "ph": 6.6, "tds_ppm": 305.0},
                  "vision": {"fish_count": 6, "avg_activity": 0.010}},
        acceptable={"get_sensor_trend", "query_knowledge_base"},
        source=StaticDataSource(_falling("ph", 6.1, 6.6), _vision()),
    ),
    Scenario(
        name="low activity + falling TDS (new-C)",
        snapshot={"sensor": {"temperature_c": 18.4, "dissolved_oxygen_mgl": 7.7,
                             "ph": 7.1, "tds_ppm": 250.0},
                  "vision": {"fish_count": 6, "avg_activity": 0.0008}},
        acceptable={"get_fish_activity", "get_sensor_trend", "query_knowledge_base"},
        source=StaticDataSource(_falling("tds_ppm", 320.0, 250.0), _vision(act=0.0008)),
    ),
    Scenario(
        name="borderline but safe on all axes (new-D)",
        # Every value sits close to a safe-range edge (16-21C, 6-12mg/L,
        # 6.5-8.0 pH, 200-450 ppm) yet all are inside the safe range -- like
        # "everything normal", calling no tool is correct and calling one is
        # not wrong; this checks restraint isn't a fluke of one comfortably-
        # mid-range fixture.
        snapshot={"sensor": {"temperature_c": 20.7, "dissolved_oxygen_mgl": 6.3,
                             "ph": 7.85, "tds_ppm": 210.0},
                  "vision": {"fish_count": 6, "avg_activity": 0.0025}},
        acceptable=set(),
        source=StaticDataSource(_sensors(temperature_c=20.7, dissolved_oxygen_mgl=6.3,
                                          ph=7.85, tds_ppm=210.0), _vision(act=0.0025)),
    ),
)
