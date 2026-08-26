"""
Retrain decision and promotion gate.

The gate is the part worth testing hardest. Drift says the world changed; it does
not say a replacement would be better, and a pipeline that ships on drift alone is
how a system gets quietly worse.

    python -m pytest mlops/test_retrain.py -v

Only needs pytest.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mlops.drift import REFERENCE, classify, load_reference, psi  # noqa: E402
from mlops.retrain import MIN_IMPROVEMENT, MIN_WINDOW, decide, gate  # noqa: E402


def _u(n, lo, hi, seed):
    r = random.Random(seed)
    return [r.uniform(lo, hi) for _ in range(n)]


# ── The detector must not cry wolf on its own data ───────────────────────────

@pytest.mark.skipif(not REFERENCE.exists(), reason="reference not captured")
def test_no_false_positive_on_a_split_of_the_reference():
    """Two halves of the same detections must not read as drift.

    This is the check that makes the thresholds credible. If a detector fires on
    a re-sample of the very data it was calibrated on, every alert afterwards is
    noise. Measured on the shipped reference: PSI ~0.04.
    """
    reference = load_reference()
    shuffled = reference[:]
    random.Random(42).shuffle(shuffled)
    half = len(shuffled) // 2

    score, _ = psi(shuffled[:half], shuffled[half:])
    assert classify(score) == "none", f"false positive on own data: PSI {score}"


@pytest.mark.skipif(not REFERENCE.exists(), reason="reference not captured")
@pytest.mark.parametrize("window", [200, 500, 1000])
def test_real_subsamples_do_not_trigger(window):
    reference = load_reference()
    sample = random.Random(7).sample(reference, min(window, len(reference)))
    assert decide(sample, reference).action == "none"


# ── Decision ─────────────────────────────────────────────────────────────────

def test_a_thin_window_is_not_a_verdict():
    """Too few detections means no conclusion, not 'no drift'."""
    d = decide(_u(MIN_WINDOW - 1, 0.1, 0.3, seed=1), _u(1000, 0.6, 0.9, seed=2))
    assert d.action == "none"
    assert "too small" in d.reason
    assert d.drift_psi is None, "no PSI should be claimed from an unusable window"


def test_collapsed_confidence_asks_for_a_retrain():
    d = decide(_u(600, 0.05, 0.30, seed=3), _u(1500, 0.60, 0.90, seed=4))
    assert d.action == "retrain"
    assert d.drift_severity == "significant"


def test_stable_production_asks_for_nothing():
    reference = _u(1500, 0.50, 0.90, seed=5)
    d = decide(_u(800, 0.50, 0.90, seed=6), reference)
    assert d.action == "none"


# ── Promotion gate ───────────────────────────────────────────────────────────

def test_a_clear_improvement_ships():
    ok, msg = gate(0.8500, 0.8395)
    assert ok and "beats" in msg


def test_an_improvement_inside_the_noise_band_does_not_ship():
    """Training noise produces small positive deltas about half the time.
    Shipping on those is a coin flip presented as a decision."""
    ok, msg = gate(0.8395 + MIN_IMPROVEMENT / 2, 0.8395)
    assert not ok
    assert "noise band" in msg


def test_a_regression_does_not_ship():
    ok, msg = gate(0.8200, 0.8395)
    assert not ok and "does not beat" in msg


def test_the_gate_separates_below_from_above_the_band():
    """Just inside the band fails, clearly outside it passes.

    The exact-boundary case is deliberately not asserted: `incumbent +
    MIN_IMPROVEMENT` is not representable in binary floating point, so a test on
    it would be pinning float arithmetic rather than the promotion rule.
    """
    incumbent = 0.8395
    assert not gate(incumbent + MIN_IMPROVEMENT * 0.9, incumbent)[0]
    assert gate(incumbent + MIN_IMPROVEMENT * 1.5, incumbent)[0]
