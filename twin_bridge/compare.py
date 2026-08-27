"""
Run S.U.R.E.'s rule engine against the twin's plant and compare it to the PLC.

This is the reason for connecting at all. Two independent implementations of the
same safety intent now watch the same tank: `backend/rules.py` here, and the
IEC 61131-3 logic in the twin's CODESYS project. They were written separately,
from the same domain, without reference to each other.

Where they agree, that is evidence. **Where they disagree, that is a finding** —
one of the two has a threshold or a precedence rule wrong, and the disagreement
says exactly which parameter to argue about. A single implementation can only be
checked against its own tests; two can be checked against each other.

The comparison is deliberately not symmetric in what it claims. S.U.R.E.'s
`critical` and the PLC's alarm bits are different vocabularies: the PLC raises a
bit per cause, S.U.R.E. produces one severity for the tank. So the mapping is
stated explicitly below rather than assumed, and cases the mapping cannot express
are reported as such instead of being forced into agreement.

    python -m twin_bridge.compare --watch          # live against the twin
    python -m twin_bridge.compare --replay f.json  # offline, from a capture
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))

from .client import ModbusTwin, TwinUnavailable  # noqa: E402
from .registers import to_sure_snapshot  # noqa: E402

# How the two vocabularies line up.
#
# The PLC's DO-low bit and S.U.R.E.'s `critical` are the same claim: oxygen is
# out of band and something must happen now. Its ammonia and temperature bits
# have no S.U.R.E. equivalent at `critical` — ammonia because there is no sensor
# for it, temperature because the rule engine treats it as a warning by design.
# Those are listed as *expected* divergences so they do not drown the real ones.
EXPECTED_DIVERGENCE = {
    "ammonia high": "S.U.R.E. has no ammonia sensor; the twin models it",
    "temperature out of band": "S.U.R.E. treats temperature as warning, not critical",
    "stress high": "the twin derives stress from chemistry; S.U.R.E. has no equivalent",
}


@dataclass
class Divergence:
    timestamp: float
    sure_status: str
    plc_alarms: list[str]
    sensor: dict
    kind: str          # "expected" | "unexplained"
    note: str


@dataclass
class Comparison:
    samples: int = 0
    agree: int = 0
    expected: int = 0
    unexplained: list[Divergence] = field(default_factory=list)
    status_counts: Counter = field(default_factory=Counter)

    def summary(self) -> str:
        if not self.samples:
            return "no samples"
        pct = 100 * self.agree / self.samples
        return (
            f"{self.samples} samples · agree {self.agree} ({pct:.1f}%) · "
            f"expected divergence {self.expected} · "
            f"unexplained {len(self.unexplained)}"
        )


def compare_once(holding: dict, inputs: dict) -> tuple[str, list[str], str, str]:
    """One sample. Returns (sure_status, plc_alarms, kind, note)."""
    import rules

    snapshot = to_sure_snapshot(holding)
    verdict = rules.evaluate(snapshot["sensor"], snapshot["vision"])
    status = verdict["status"]
    alarms = list(inputs.get("alarms", []))

    do_low = "dissolved oxygen low" in alarms
    sure_critical = status == "critical"

    if do_low == sure_critical:
        # The claims that map onto each other line up. Anything else the PLC
        # raised is only expected divergence if we have a stated reason.
        others = [a for a in alarms if a != "dissolved oxygen low"]
        unexplained = [a for a in others if a not in EXPECTED_DIVERGENCE]
        if unexplained:
            return status, alarms, "unexplained", f"PLC raised {unexplained} with no mapping"
        if others:
            return status, alarms, "expected", "; ".join(EXPECTED_DIVERGENCE[a] for a in others)
        return status, alarms, "agree", ""

    if do_low and not sure_critical:
        return status, alarms, "unexplained", (
            f"PLC says oxygen low, S.U.R.E. says {status} "
            f"(DO {holding['dissolved_oxygen_mgl']:.2f} mg/L)"
        )
    return status, alarms, "unexplained", (
        f"S.U.R.E. says critical, PLC raised no oxygen alarm "
        f"(DO {holding['dissolved_oxygen_mgl']:.2f} mg/L)"
    )


def run(source, samples: int, interval: float, quiet: bool = False) -> Comparison:
    result = Comparison()

    for _ in range(samples):
        try:
            holding, inputs = source.read()
        except TwinUnavailable as exc:
            print(f"twin unavailable: {exc}")
            break

        status, alarms, kind, note = compare_once(holding, inputs)
        result.samples += 1
        result.status_counts[status] += 1

        if kind == "agree":
            result.agree += 1
        elif kind == "expected":
            result.expected += 1
        else:
            result.unexplained.append(Divergence(
                timestamp=time.time(), sure_status=status, plc_alarms=alarms,
                sensor=holding, kind=kind, note=note,
            ))

        if not quiet:
            mark = {"agree": "=", "expected": "~", "unexplained": "!"}[kind]
            print(f"  {mark} DO {holding['dissolved_oxygen_mgl']:5.2f}  "
                  f"S.U.R.E. {status:8}  PLC {alarms or ['-']}"
                  + (f"   {note}" if note else ""))

        if interval:
            time.sleep(interval)

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Compare S.U.R.E. against the twin's PLC")
    ap.add_argument("--watch", action="store_true", help="live against the twin")
    ap.add_argument("--replay", metavar="FILE", help="offline, from a capture")
    ap.add_argument("--samples", type=int, default=60)
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args()

    if args.replay:
        from .client import FakeTwin

        payload = json.loads(Path(args.replay).read_text(encoding="utf-8"))
        source = FakeTwin(payload["holding"], payload["input"])
        interval = 0.0
    elif args.watch:
        source = ModbusTwin()
        interval = args.interval
    else:
        ap.print_help()
        return 1

    print("Comparing S.U.R.E.'s rule engine against the twin's PLC\n")
    result = run(source, args.samples, interval)
    source.close()

    print(f"\n{result.summary()}")
    print(f"S.U.R.E. verdicts: {dict(result.status_counts)}")

    if result.unexplained:
        print(f"\nUnexplained divergences ({len(result.unexplained)}) — these are the"
              f" ones worth arguing about:")
        for d in result.unexplained[:10]:
            print(f"  DO {d.sensor['dissolved_oxygen_mgl']:.2f} mg/L, "
                  f"temp {d.sensor['temperature_c']:.1f} — {d.note}")
    elif result.samples:
        print("\nNo unexplained divergence: the two engines agree wherever their "
              "vocabularies overlap.")

    if args.json:
        Path(args.json).write_text(json.dumps({
            "samples": result.samples,
            "agree": result.agree,
            "expected_divergence": result.expected,
            "unexplained": [
                {"sure": d.sure_status, "plc": d.plc_alarms,
                 "sensor": d.sensor, "note": d.note}
                for d in result.unexplained
            ],
        }, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
