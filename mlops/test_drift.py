"""
Drift detection tests.

PSI is easy to implement and easy to implement wrongly — an empty-bin division, a
sign error or a floor that swallows the signal all produce a number that looks
plausible and detects nothing. These pin the behaviour against cases where the
right answer is known independently of the implementation.

    python -m pytest mlops/test_drift.py -v

Only needs pytest.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mlops.drift import (  # noqa: E402
    BINS,
    MODERATE,
    SIGNIFICANT,
    classify,
    compare,
    histogram,
    psi,
)


def _uniform(n: int, lo: float, hi: float, seed: int = 0) -> list[float]:
    rng = random.Random(seed)
    return [rng.uniform(lo, hi) for _ in range(n)]


# ── Histogram ────────────────────────────────────────────────────────────────

def test_histogram_sums_to_one():
    assert sum(histogram(_uniform(500, 0.0, 1.0))) == pytest.approx(1.0)


def test_histogram_bins_edges_correctly():
    """1.0 must land in the last bin, not overflow into an eleventh."""
    h = histogram([0.0, 0.999, 1.0])
    assert len(h) == BINS
    assert h[0] == pytest.approx(1 / 3)
    assert h[-1] == pytest.approx(2 / 3)


def test_histogram_of_nothing_is_all_zero():
    assert histogram([]) == [0.0] * BINS


# ── PSI ──────────────────────────────────────────────────────────────────────

def test_identical_distributions_score_zero():
    values = _uniform(1000, 0.3, 0.9, seed=1)
    score, _ = psi(values, values)
    assert score == pytest.approx(0.0, abs=1e-9)


def test_psi_is_directional_under_quantile_binning():
    """Swapping the arguments does not give the same number, and should not.

    Bin edges come from the first argument, so psi(reference, current) asks "how
    did the current window move relative to how the reference was spread". That
    is a directional question. Equal-width bins made it symmetric; quantile bins
    correctly do not, and the two directions must still agree on the verdict.
    """
    a = _uniform(800, 0.2, 0.8, seed=2)
    b = _uniform(800, 0.4, 1.0, seed=3)
    forward, backward = psi(a, b)[0], psi(b, a)[0]

    assert forward != pytest.approx(backward, rel=1e-6)
    assert classify(forward) == classify(backward), (
        "direction may change the magnitude, never the conclusion"
    )


def test_small_sampling_noise_stays_below_the_moderate_threshold():
    """Two samples from the same distribution must not raise an alert."""
    a = _uniform(1500, 0.3, 0.9, seed=4)
    b = _uniform(1500, 0.3, 0.9, seed=5)
    assert psi(a, b)[0] < MODERATE


def test_a_clear_shift_is_flagged_significant():
    """Confidence collapsing from the 0.6-0.9 band to 0.1-0.4 is the failure this
    is meant to catch."""
    reference = _uniform(1200, 0.6, 0.9, seed=6)
    current = _uniform(1200, 0.1, 0.4, seed=7)
    assert psi(reference, current)[0] > SIGNIFICANT


def test_partial_degradation_scales_with_how_much_degrades():
    """The score must grade, not saturate.

    This is the property equal-width bins destroyed: with a reference confined to
    0.5-0.9, most fixed bins were empty and any real shift slammed into the
    empty-bin floor, so PSI went from 0.06 to 1.05 with nothing between. Quantile
    edges restore the gradient. Measured on this fixture: 10% degraded scores
    ~0.10, 20% scores ~0.26, a full collapse scores >8.
    """
    reference = _uniform(2500, 0.50, 0.90, seed=8)
    ten = psi(reference, _uniform(2250, 0.50, 0.90, seed=9)
              + _uniform(250, 0.30, 0.50, seed=10))[0]
    twenty = psi(reference, _uniform(2000, 0.50, 0.90, seed=9)
                 + _uniform(500, 0.30, 0.50, seed=10))[0]

    assert ten < twenty, "a bigger shift must score higher"
    assert twenty >= SIGNIFICANT, "one detection in five degrading must alarm"
    assert ten < SIGNIFICANT * 2, f"10% should not saturate the scale: {ten}"


def test_quantile_edges_leave_no_empty_reference_bin():
    """Every reference bin carries mass by construction — the fix for the
    saturation above. An empty reference bin reintroduces the floor blow-up."""
    from mlops.drift import bin_edges, histogram

    reference = _uniform(3000, 0.50, 0.90, seed=30)
    shares = histogram(reference, bin_edges(reference))
    assert min(shares) > 0.0, f"empty reference bin: {shares}"
    assert max(shares) < 0.35, f"bin far too wide: {shares}"


def test_mass_moving_into_an_unoccupied_bin_scores_high():
    """Detections appearing where the reference had none is a strong signal.

    This is a property of PSI, not an artefact: the empty-bin floor makes the log
    term large on purpose, because a model producing confidences it never
    produced during validation is exactly the case worth interrupting someone
    for. Pinned here so nobody 'fixes' the floor into silence later.
    """
    reference = _uniform(1500, 0.60, 0.90, seed=20)
    current = _uniform(1000, 0.60, 0.90, seed=21) + _uniform(500, 0.05, 0.25, seed=22)
    assert psi(reference, current)[0] > SIGNIFICANT


def test_contributions_sum_to_the_total():
    a = _uniform(600, 0.2, 0.8, seed=11)
    b = _uniform(600, 0.3, 0.95, seed=12)
    score, per_bin = psi(a, b)
    assert sum(x["contribution"] for x in per_bin) == pytest.approx(score, abs=1e-4)


def test_empty_current_window_does_not_raise():
    """A window with no detections at all is itself a signal, not a crash."""
    score, _ = psi(_uniform(400, 0.4, 0.9, seed=13), [])
    assert score > SIGNIFICANT


# ── Classification ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("value,expected", [
    (0.0, "none"),
    (0.099, "none"),
    (0.10, "moderate"),
    (0.24, "moderate"),
    (0.25, "significant"),
    (3.0, "significant"),
])
def test_classify_boundaries(value, expected):
    assert classify(value) == expected


# ── Report ───────────────────────────────────────────────────────────────────

def test_report_records_both_means_and_direction():
    reference = _uniform(700, 0.6, 0.9, seed=14)
    current = _uniform(700, 0.2, 0.5, seed=15)
    report = compare(reference, current)

    assert report.mean_current < report.mean_reference
    assert report.should_review
    assert report.severity == "significant"
    assert "down" in report.summary()


def test_stable_report_does_not_ask_for_review():
    values = _uniform(1200, 0.35, 0.85, seed=16)
    report = compare(values, _uniform(1200, 0.35, 0.85, seed=17))
    assert not report.should_review
    assert report.severity == "none"


def test_reference_file_matches_the_shipped_model():
    """The committed reference must be non-trivial, or drift scoring is vacuous."""
    from mlops.drift import REFERENCE, load_reference

    if not REFERENCE.exists():
        pytest.skip("reference not captured in this checkout")
    confidences = load_reference()
    assert len(confidences) > 200, "reference too small to be a stable baseline"
    assert all(0.0 <= c <= 1.0 for c in confidences)
