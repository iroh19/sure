"""
Does S.U.R.E.'s advice change the outcome?

Every other measurement in this repository grades a component: how well the
detector detects, how well retrieval retrieves, how often the model agrees with
the rule engine. None of them answers the question the project exists to answer —
whether acting on the advice leaves the fish better off. This one does, by
running the same plant twice and changing exactly one thing.

    arm A   the plant runs on its own controller
    arm B   the same plant, same scenario, but each tick S.U.R.E. evaluates the
            state with backend/rules.py and publishes its severity as the stress
            index the controller already consumes

The controller raises its aeration setpoint when stress is high, so a `warning`
from S.U.R.E. opens the aerator before the oxygen alarm would. That is the whole
mechanism: one register, one setpoint, measurable consequences.

WHAT THIS IS AND IS NOT

The plant here is `fake_plc.Plant`, a stand-in. The numbers below characterise
that fixture's controller, not a fish farm — the real digital twin has a virtual
clock, APHA oxygen saturation, feed-to-ammonia conversion and biomass growth.
What this establishes is the *mechanism and the harness*: the same command run
against the real CODESYS PLC produces the real result.

The transport is deliberately not in the loop. `client.py` writing HR6 over
Modbus is verified separately by its own tests; putting a socket inside the
experiment would make it slow and non-deterministic without measuring anything
extra. Both arms use the real `backend/rules.py`, which is the part under test.

    python -m twin_bridge.experiment
    python -m twin_bridge.experiment --scenario decline --ticks 400
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))

from .advisor import SEVERITY_TO_STRESS, Advisor  # noqa: E402
from .fake_plc import DO_ALARM_BELOW, SCENARIOS, Plant  # noqa: E402
from .registers import decode_holding  # noqa: E402

@dataclass
class ArmResult:
    label: str
    ticks: int
    min_do: float
    ticks_below_threshold: int
    ticks_in_alarm: int
    aeration_cost: float        # mean aerator %, a stand-in for energy
    final_do: float

    def summary(self) -> str:
        return (
            f"{self.label:<28} min DO {self.min_do:5.2f}  "
            f"eşik altı {self.ticks_below_threshold:4d} tick  "
            f"alarm {self.ticks_in_alarm:4d}  "
            f"aerasyon {self.aeration_cost:5.1f}%"
        )


def run_arm(label: str, scenario: str, ticks: int, advise: bool,
            lead_ticks: int | None = None) -> ArmResult:
    """Run the plant once.

    `advise=False` is the controller alone. With `lead_ticks=None` the advisor
    publishes only the rule engine's severity — the original arm, kept because it
    is what showed the lever doing nothing. With a lead time it also projects the
    slope forward, which is the change that measurement justified.
    """
    import rules

    plant = Plant(scenario)
    advisor = Advisor(threshold=DO_ALARM_BELOW,
                      lead_ticks=lead_ticks if lead_ticks is not None else 0)

    for _ in range(ticks):
        holding, _ = plant.step()

        if advise:
            reading = decode_holding(holding)
            verdict = rules.evaluate(
                {
                    "temperature_c": reading["temperature_c"],
                    "dissolved_oxygen_mgl": reading["dissolved_oxygen_mgl"],
                    "ph": reading["ph"],
                    "tds_ppm": reading["tds_ppm"],
                },
                None,
            )
            # Fed back on the next tick, which is how a real advisory loop
            # behaves: the controller acts on the previous reading, never on a
            # value derived from the state it is about to produce.
            if lead_ticks is None:
                plant.stress = SEVERITY_TO_STRESS[verdict["status"]]
            else:
                plant.stress = advisor.stress_for(
                    reading["dissolved_oxygen_mgl"], verdict["status"])

    dos = [h["do"] for h in plant.history]
    return ArmResult(
        label=label,
        ticks=len(plant.history),
        min_do=round(min(dos), 3),
        ticks_below_threshold=sum(1 for d in dos if d < DO_ALARM_BELOW),
        ticks_in_alarm=sum(1 for h in plant.history if h["alarm"]),
        aeration_cost=round(sum(h["aerator"] for h in plant.history) / len(plant.history), 2),
        final_do=round(dos[-1], 3),
    )


def compare(scenario: str, ticks: int,
            lead_ticks: int | None = None) -> tuple[ArmResult, ArmResult]:
    baseline = run_arm("A — kontrolör tek başına", scenario, ticks, advise=False)
    label = ("B — S.U.R.E. devrede" if lead_ticks is None
             else f"B — S.U.R.E. + trend ({lead_ticks} tick)")
    advised = run_arm(label, scenario, ticks, advise=True, lead_ticks=lead_ticks)
    return baseline, advised


def sweep(scenario: str, ticks: int, leads: list[int]) -> None:
    """How much lead time is worth buying?

    Acting earlier means more aeration for longer. The point of sweeping rather
    than picking is that the trade is visible: somewhere the extra energy stops
    buying meaningful oxygen, and that elbow is the setting to ship.
    """
    base = run_arm("A", scenario, ticks, advise=False)
    print(f"  {'öngörü':>8}  {'eşik altı':>10}  {'değişim':>8}  {'en düşük DO':>12}  "
          f"{'aerasyon':>9}  {'ek maliyet':>11}")
    print(f"  {'yok':>8}  {base.ticks_below_threshold:10d}  {'—':>8}  "
          f"{base.min_do:12.2f}  {base.aeration_cost:8.1f}%  {'—':>11}")

    for lead in leads:
        r = run_arm("B", scenario, ticks, advise=True, lead_ticks=lead)
        d = r.ticks_below_threshold - base.ticks_below_threshold
        pct = d / max(base.ticks_below_threshold, 1) * 100
        print(f"  {lead:8d}  {r.ticks_below_threshold:10d}  {pct:+7.1f}%  "
              f"{r.min_do:12.2f}  {r.aeration_cost:8.1f}%  "
              f"{r.aeration_cost - base.aeration_cost:+10.2f}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Does the advice change the outcome?")
    ap.add_argument("--scenario", default="decline", choices=sorted(SCENARIOS))
    ap.add_argument("--ticks", type=int, default=300)
    ap.add_argument("--lead", type=int, default=None,
                    help="trend öngörü penceresi (tick); verilmezse yalnızca severity")
    ap.add_argument("--sweep", action="store_true",
                    help="öngörü penceresini tara ve takası göster")
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args()

    if args.sweep:
        print(f"Senaryo: {args.scenario} · {args.ticks} tick · eşik {DO_ALARM_BELOW} mg/L")
        print("Öngörü penceresi ne kadar erken açmaya değer?\n")
        sweep(args.scenario, args.ticks, [10, 20, 30, 45, 60, 90])
        print("\n  NOT: plant `fake_plc.Plant`, gerçek ikiz değil.")
        return 0

    print(f"Senaryo: {args.scenario} · {args.ticks} tick · eşik {DO_ALARM_BELOW} mg/L")
    print("Tek değişken: S.U.R.E.'nin severity'si HR6'ya yazılıyor mu\n")

    a, b = compare(args.scenario, args.ticks, args.lead)
    print("  " + a.summary())
    print("  " + b.summary())

    d_below = b.ticks_below_threshold - a.ticks_below_threshold
    d_alarm = b.ticks_in_alarm - a.ticks_in_alarm
    d_cost = b.aeration_cost - a.aeration_cost
    d_min = b.min_do - a.min_do

    print("\n  fark:")
    print(f"    eşik altı süre   {d_below:+d} tick"
          + (f"  ({abs(d_below) / max(a.ticks_below_threshold, 1) * 100:.0f}% "
             f"{'azalma' if d_below < 0 else 'artış'})" if a.ticks_below_threshold else ""))
    print(f"    alarm süresi     {d_alarm:+d} tick")
    print(f"    en düşük DO      {d_min:+.3f} mg/L")
    print(f"    aerasyon maliyeti {d_cost:+.2f} puan")

    print()
    if d_below < 0 and d_min > 0:
        print("  S.U.R.E. devredeyken oksijen eşiğin altında daha az kaldı ve dip nokta")
        print("  yükseldi. Bedeli daha fazla aerasyon — takas ölçülebilir durumda.")
    elif d_below == 0 and d_alarm == 0:
        print("  Fark yok: bu senaryoda kaldıraç devreye girmiyor. Kural motoru")
        print("  kontrolörden daha erken uyarmıyorsa yazacak bir şey de yok.")
    else:
        print("  S.U.R.E. devredeyken sonuç iyileşmedi. Bu da bir sonuç — eşik")
        print("  eşlemesi ya da kaldıracın kendisi yeniden düşünülmeli.")

    print("\n  NOT: plant `fake_plc.Plant`, gerçek ikiz değil. Bu sayılar mekanizmayı")
    print("  ve düzeneği doğrular; gerçek sonuç için aynı komut CODESYS PLC'ye karşı")
    print("  koşturulmalı.")

    if args.json:
        Path(args.json).write_text(json.dumps({
            "scenario": args.scenario, "ticks": args.ticks,
            "baseline": asdict(a), "advised": asdict(b),
            "delta": {"ticks_below_threshold": d_below, "ticks_in_alarm": d_alarm,
                      "min_do": round(d_min, 3), "aeration_cost": round(d_cost, 2)},
            "caveat": "plant is fake_plc.Plant, a stand-in for the CODESYS twin",
        }, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\n  JSON: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
