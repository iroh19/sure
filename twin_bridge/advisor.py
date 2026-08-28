"""
What stress index to publish, given the verdict and the trend.

The A/B experiment showed the advisory layer changing almost nothing: S.U.R.E.
and the controller fire at the same reading, so publishing the rule engine's
severity told the controller something it already knew. An early-warning system
earns its place by warning *early*, which means using information the controller
does not have.

The controller sees a level. This sees a **slope**, and projects when the level
will cross the threshold.

`backend/rules.py` is deliberately untouched. It still owns the verdict, its
thresholds are still the documented ones, and severity is still only ever
escalated. This layer decides what to *publish* to the controller, which is a
different question from what the tank's condition *is*. Folding trend into the
rule engine would change every threshold claim in the documentation and put a
predictive signal inside a safety guarantee, where it does not belong: a
projection can be wrong, and a projection that escalates a verdict would let a
noisy slope declare an emergency.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

# Severity floor, as before. `ok` publishes nothing, and the trend can lift it.
SEVERITY_TO_STRESS = {"ok": 0, "warning": 70, "critical": 95}

# Slope is estimated over this many readings. Long enough that a single noisy
# sample cannot fake a trend, short enough to react inside a crash.
WINDOW = 10

# What to publish when the projection says the threshold is close. Below the
# `warning` level on purpose: a prediction should open the aerator, not claim
# the same confidence as an out-of-band measurement.
PREDICTIVE_STRESS = 65

# A slope smaller than this is treated as flat. Without it, sensor jitter alone
# produces a projected crossing and the aerator never closes.
MIN_SLOPE = 0.002


# Default from the sweep in `experiment.py --sweep`, not from intuition. On the
# crash scenario every lead time from 10 ticks upward buys the same reduction in
# time below threshold (-8.1%), while aeration cost keeps climbing. Ten is the
# elbow: the shortest lead that captures the whole benefit.
DEFAULT_LEAD_TICKS = 10


@dataclass
class Advisor:
    """Stateful: it has to remember the last few readings to see a slope."""
    threshold: float
    lead_ticks: int = DEFAULT_LEAD_TICKS
    window: int = WINDOW
    _history: deque = field(default_factory=lambda: deque(maxlen=WINDOW))

    def __post_init__(self):
        self._history = deque(maxlen=self.window)

    def slope(self) -> float:
        """Change per tick. Negative means falling.

        First-versus-second half rather than a least-squares fit: the difference
        is immaterial over ten points, and halves make the intent readable.
        """
        if len(self._history) < self.window:
            return 0.0
        mid = self.window // 2
        first = sum(list(self._history)[:mid]) / mid
        second = sum(list(self._history)[mid:]) / (self.window - mid)
        return (second - first) / (self.window / 2)

    def ticks_to_threshold(self, current: float) -> float | None:
        """How long until the level crosses, at the present slope. None if it
        is not heading there."""
        s = self.slope()
        if s >= -MIN_SLOPE or current <= self.threshold:
            return None
        return (current - self.threshold) / -s

    def stress_for(self, dissolved_oxygen: float, verdict_status: str) -> int:
        """The index to publish this tick."""
        self._history.append(dissolved_oxygen)
        floor = SEVERITY_TO_STRESS[verdict_status]

        eta = self.ticks_to_threshold(dissolved_oxygen)
        predictive = PREDICTIVE_STRESS if (eta is not None and eta <= self.lead_ticks) else 0

        # The verdict is a floor, never a ceiling. A prediction can raise the
        # published stress but must never lower what a measured breach already
        # justifies.
        return max(floor, predictive)

    def explain(self, dissolved_oxygen: float, verdict_status: str) -> str:
        eta = self.ticks_to_threshold(dissolved_oxygen)
        if eta is None:
            return f"{verdict_status}, eğilim tehdit değil"
        return (f"{verdict_status}, mevcut eğimle eşiğe ~{eta:.0f} tick kaldı "
                f"(eğim {self.slope():+.4f}/tick)")
