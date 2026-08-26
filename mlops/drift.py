"""
Detect when the detector has stopped seeing what it was trained on.

The tank does not stay still: water clarity changes, lighting changes, and the
fish grow. None of that produces an error — the model keeps returning boxes, the
dashboard keeps showing numbers, and accuracy quietly falls. Labels are not
available in production, so drift has to be inferred from the model's own output.

**Population Stability Index** over the detection-confidence distribution. PSI
compares a reference histogram, captured on the validation set at training time,
against a recent production window:

    PSI = sum over bins of (current% - reference%) * ln(current% / reference%)

The usual reading, and the one used here:

    < 0.10   no meaningful shift
    0.10-0.25 moderate — worth watching
    > 0.25   significant — investigate, consider retraining

Confidence was chosen over fish_count because count is confounded by the thing
being measured: fewer fish detected may mean the model degraded, or may mean
fewer fish are in frame. The confidence distribution is a property of the model's
response, not of the stock.

PSI is a **signal, not a verdict**. It says the input the model sees has changed;
it cannot say accuracy dropped, because that needs labels. A high PSI should open
a review, not fire a retrain on its own — that is why `retrain_dag.py` gates the
retrain behind the evaluation harness rather than behind this number.

    python -m mlops.drift --reference          # capture reference from the val set
    python -m mlops.drift --check recent.json  # score a production window
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REFERENCE = REPO / "mlops" / "reference_confidence.json"

# Ten bins, with edges taken from the reference's own deciles rather than spread
# evenly over [0, 1].
#
# Equal-width bins were the first implementation and they made the metric useless
# here. The detector's confidences sit in roughly 0.5-0.9, so six of ten fixed
# bins were empty in the reference; any shift landing in one of them hit the
# empty-bin floor and the log term exploded. Calibration showed PSI jumping
# straight from 0.06 to 1.05 with nothing in between — the "moderate" band was
# unreachable and the signal was a binary alarm dressed as a gradient.
#
# Quantile edges give every reference bin ~10% of the mass by construction, so no
# bin is empty and PSI grades shifts instead of saturating.
BINS = 10

# Still needed for the current window, which can legitimately empty a bin.
EPSILON = 1e-4

MODERATE = 0.10
SIGNIFICANT = 0.25


@dataclass(frozen=True)
class DriftReport:
    psi: float
    severity: str          # "none" | "moderate" | "significant"
    reference_n: int
    current_n: int
    mean_reference: float
    mean_current: float
    per_bin: list[dict]

    @property
    def should_review(self) -> bool:
        return self.psi >= MODERATE

    def summary(self) -> str:
        arrow = "down" if self.mean_current < self.mean_reference else "up"
        return (
            f"PSI {self.psi:.4f} ({self.severity}) — "
            f"mean confidence {self.mean_reference:.3f} -> {self.mean_current:.3f} ({arrow}), "
            f"{self.current_n} detections against a {self.reference_n}-detection reference"
        )


def bin_edges(reference: list[float], bins: int = BINS) -> list[float]:
    """Interior bin edges at the reference's quantiles.

    Returns bins-1 cut points. Duplicates are removed: if the reference is
    degenerate enough that two quantiles coincide, collapsing them is better than
    creating a zero-width bin that can never be populated.
    """
    if not reference:
        return [i / bins for i in range(1, bins)]
    ordered = sorted(reference)
    edges = []
    for i in range(1, bins):
        idx = min(len(ordered) - 1, int(round(i / bins * (len(ordered) - 1))))
        edges.append(ordered[idx])
    return sorted(set(edges))


def histogram(values: list[float], edges: list[float] | None = None,
              bins: int = BINS) -> list[float]:
    """Share of values per bin, using the given interior edges."""
    if edges is None:
        edges = [i / bins for i in range(1, bins)]
    n_bins = len(edges) + 1
    if not values:
        return [0.0] * n_bins

    counts = [0] * n_bins
    for v in values:
        idx = 0
        while idx < len(edges) and v > edges[idx]:
            idx += 1
        counts[idx] += 1
    total = len(values)
    return [c / total for c in counts]


def psi(reference: list[float], current: list[float]) -> tuple[float, list[dict]]:
    """Population Stability Index between two distributions of confidences.

    Bin edges come from the reference, so the comparison asks "where did the
    current window's mass go relative to how the reference was spread", which is
    the question drift is about.
    """
    edges = bin_edges(reference)
    ref_h = histogram(reference, edges)
    cur_h = histogram(current, edges)

    total = 0.0
    per_bin: list[dict] = []
    for i, (r, c) in enumerate(zip(ref_h, cur_h)):
        r_adj, c_adj = max(r, EPSILON), max(c, EPSILON)
        contribution = (c_adj - r_adj) * math.log(c_adj / r_adj)
        total += contribution
        lo = "-inf" if i == 0 else f"{edges[i - 1]:.3f}"
        hi = "+inf" if i == len(edges) else f"{edges[i]:.3f}"
        per_bin.append({
            "bin": f"{lo}..{hi}",
            "reference": round(r, 4),
            "current": round(c, 4),
            "contribution": round(contribution, 5),
        })
    return total, per_bin


def classify(value: float) -> str:
    if value >= SIGNIFICANT:
        return "significant"
    if value >= MODERATE:
        return "moderate"
    return "none"


def compare(reference: list[float], current: list[float]) -> DriftReport:
    value, per_bin = psi(reference, current)
    return DriftReport(
        psi=round(value, 4),
        severity=classify(value),
        reference_n=len(reference),
        current_n=len(current),
        mean_reference=round(sum(reference) / len(reference), 4) if reference else 0.0,
        mean_current=round(sum(current) / len(current), 4) if current else 0.0,
        per_bin=per_bin,
    )


# ── Reference capture ────────────────────────────────────────────────────────

def capture_reference(weights: Path, images_dir: Path, device: str = "mps") -> list[float]:
    """Collect the confidence distribution the model produces on the val set.

    The reference has to come from the same data the reported metrics come from,
    or the baseline means something different from what the model card claims.
    """
    from ultralytics import YOLO

    model = YOLO(str(weights))
    confidences: list[float] = []
    paths = sorted(p for p in images_dir.iterdir()
                   if p.suffix.lower() in {".jpg", ".jpeg", ".png"})

    for path in paths:
        res = model.predict(str(path), device=device, verbose=False)[0]
        if res.boxes is not None and len(res.boxes):
            confidences.extend(float(c) for c in res.boxes.conf.tolist())

    return confidences


def load_reference(path: Path = REFERENCE) -> list[float]:
    if not path.exists():
        raise FileNotFoundError(
            f"No reference distribution at {path}. Capture one with:\n"
            f"  python -m mlops.drift --reference"
        )
    return json.loads(path.read_text(encoding="utf-8"))["confidences"]


def main() -> int:
    ap = argparse.ArgumentParser(description="Detection-confidence drift")
    ap.add_argument("--reference", action="store_true",
                    help="capture the reference distribution from the validation set")
    ap.add_argument("--check", metavar="FILE",
                    help="JSON file with a 'confidences' list to score")
    ap.add_argument("--device", default="mps")
    args = ap.parse_args()

    if args.reference:
        weights = REPO / "sure_models" / "sure_v1" / "weights" / "best.pt"
        images = REPO / "data" / "sure_dataset" / "val" / "images"
        if not weights.exists() or not images.is_dir():
            print(f"Need {weights.name} and {images}")
            return 1

        print("Capturing reference distribution from the validation set ...")
        confidences = capture_reference(weights, images, args.device)
        REFERENCE.parent.mkdir(parents=True, exist_ok=True)
        REFERENCE.write_text(json.dumps({
            "weights": "sure_models/sure_v1/weights/best.pt",
            "source": "data/sure_dataset/val/images",
            "n": len(confidences),
            "confidences": [round(c, 4) for c in confidences],
        }, indent=1), encoding="utf-8")
        mean = sum(confidences) / len(confidences)
        print(f"  {len(confidences)} detections, mean confidence {mean:.4f}")
        print(f"  wrote {REFERENCE.relative_to(REPO)}")
        return 0

    if args.check:
        payload = json.loads(Path(args.check).read_text(encoding="utf-8"))
        report = compare(load_reference(), payload["confidences"])
        print(report.summary())
        print()
        print("| bin | reference | current | contribution |")
        print("|-----|----------:|--------:|-------------:|")
        for b in report.per_bin:
            print(f"| {b['bin']} | {b['reference']} | {b['current']} | {b['contribution']} |")
        print(f"\nreview needed: {report.should_review}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
