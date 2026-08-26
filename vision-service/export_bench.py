"""
Export the detector to edge formats and measure what each one costs.

A speed number on its own is not a result. Every export format trades accuracy
for latency somewhere, and the trade is invisible unless both are measured on the
same validation set under the same conditions. So each format here is run through
the identical 98-image split that produced the baseline, and the table reports
mAP alongside milliseconds.

Formats are attempted, not assumed: anything whose toolchain is missing on this
machine is reported as skipped rather than silently dropped. TensorRT needs CUDA
and cannot run on Apple Silicon at all — `--emit-jetson` writes the script that
produces those rows on the target device.

    python export_bench.py                     # export + measure everything available
    python export_bench.py --formats onnx      # one format
    python export_bench.py --skip-export       # re-measure existing exports
    python export_bench.py --emit-jetson       # write the Jetson-side script

Notes on methodology are in `_measure`.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
WEIGHTS = REPO / "sure_models" / "sure_v1" / "weights" / "best.pt"
DATA = REPO / "data" / "sure_dataset.yaml"
EXPORT_DIR = REPO / "sure_models" / "sure_v1" / "export"

# Latency is measured on real validation frames, not random noise: NMS cost
# depends on how many boxes survive, and an empty image is the fastest possible
# case. Averaging over noise would flatter every format equally and hide the
# formats that degrade specifically on crowded frames.
LATENCY_IMAGES = 40
WARMUP = 8


@dataclass
class Row:
    name: str
    device: str
    map50: float | None = None
    map5095: float | None = None
    precision: float | None = None
    recall: float | None = None
    p50_ms: float | None = None
    p95_ms: float | None = None
    size_mb: float | None = None
    status: str = "ok"

    @property
    def fps(self) -> float | None:
        return round(1000.0 / self.p50_ms, 1) if self.p50_ms else None


def _sample_images(n: int) -> list:
    """Load validation frames into memory as arrays.

    Decoded up front on purpose. Passing file paths would put a JPEG read and
    decode inside the timed loop, and disk latency varies run to run — it would
    land in the measurement as noise that has nothing to do with the format being
    compared.
    """
    import cv2

    val_dir = REPO / "data" / "sure_dataset" / "val" / "images"
    paths = sorted(p for p in val_dir.iterdir() if p.suffix.lower() in {".jpg", ".png", ".jpeg"})
    if not paths:
        raise FileNotFoundError(f"No validation images under {val_dir}")
    frames = [cv2.imread(str(p)) for p in paths[:n]]
    return [f for f in frames if f is not None]


def _measure(model, device: str, images: list[str]) -> tuple[float, float]:
    """Return (p50, p95) inference latency in milliseconds.

    Percentiles rather than a mean, because a real-time pipeline is judged by its
    worst frames: a 15 ms average with a 90 ms tail drops frames exactly when the
    tank is crowded, which is when detection matters most.

    Warm-up runs are discarded. The first inference on any backend pays for lazy
    kernel compilation and memory allocation, and including it would make every
    format look worse than it is by a constant nobody experiences in production.
    """
    for frame in images[:WARMUP]:
        model.predict(frame, device=device, verbose=False)

    timings: list[float] = []
    for frame in images:
        t0 = time.perf_counter()
        model.predict(frame, device=device, verbose=False)
        timings.append((time.perf_counter() - t0) * 1000)

    timings.sort()
    p50 = statistics.median(timings)
    p95 = timings[min(len(timings) - 1, int(0.95 * len(timings)))]
    return round(p50, 2), round(p95, 2)


def _validate(model, device: str) -> dict:
    r = model.val(data=str(DATA), device=device, verbose=False, plots=False)
    return {
        "map50": round(float(r.box.map50), 4),
        "map5095": round(float(r.box.map), 4),
        "precision": round(float(r.box.mp), 4),
        "recall": round(float(r.box.mr), 4),
    }


def _size_mb(path: Path) -> float | None:
    if path.is_file():
        return round(path.stat().st_size / 1048576, 1)
    if path.is_dir():  # CoreML .mlpackage
        total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        return round(total / 1048576, 1)
    return None


# ── Exports ──────────────────────────────────────────────────────────────────

def export_all(formats: list[str]) -> dict[str, Path]:
    """Export and return {name: artefact path}. Failures are reported, not fatal."""
    from ultralytics import YOLO

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    produced: dict[str, Path] = {}

    for fmt in formats:
        if fmt in ("pt-mps", "pt-cpu"):
            produced[fmt] = WEIGHTS
            continue

        print(f"  exporting {fmt} ...", end=" ", flush=True)
        try:
            model = YOLO(str(WEIGHTS))
            if fmt == "onnx":
                out = Path(model.export(format="onnx", opset=12, simplify=True, verbose=False))
            elif fmt == "onnx-int8":
                base = EXPORT_DIR / "best.onnx"
                if not base.exists():
                    base = Path(YOLO(str(WEIGHTS)).export(format="onnx", opset=12,
                                                          simplify=True, verbose=False))
                out = _quantize_dynamic(base)
            elif fmt == "coreml":
                out = Path(model.export(format="coreml", verbose=False))
            elif fmt == "torchscript":
                out = Path(model.export(format="torchscript", verbose=False))
            else:
                print("unknown format, skipped")
                continue

            target = EXPORT_DIR / out.name
            if out.resolve() != target.resolve():
                if target.exists():
                    import shutil
                    shutil.rmtree(target) if target.is_dir() else target.unlink()
                out.rename(target)
            produced[fmt] = target
            print(f"ok -> {target.name}")
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED ({type(exc).__name__}: {exc})")

    return produced


def _quantize_dynamic(onnx_path: Path) -> Path:
    """INT8 weight quantization via onnxruntime.

    Dynamic quantization is used because it needs no calibration set: weights go
    to INT8 and activations are quantised per inference. TensorRT INT8 on the
    Jetson uses static calibration instead and will land differently — this row
    answers "what does INT8 cost in accuracy", not "what will the Jetson do".
    """
    from onnxruntime.quantization import QuantType, quantize_dynamic

    out = onnx_path.with_name(onnx_path.stem + "-int8.onnx")
    quantize_dynamic(str(onnx_path), str(out), weight_type=QuantType.QUInt8)
    return out


# ── Benchmark ────────────────────────────────────────────────────────────────

DEVICE_FOR = {
    "pt-mps": "mps",
    "pt-cpu": "cpu",
    "onnx": "cpu",
    "onnx-int8": "cpu",
    "coreml": "cpu",       # CoreML dispatches to ANE/GPU internally
    "torchscript": "cpu",
}


def benchmark(produced: dict[str, Path]) -> list[Row]:
    from ultralytics import YOLO

    images = _sample_images(LATENCY_IMAGES)
    rows: list[Row] = []

    for name, path in produced.items():
        device = DEVICE_FOR.get(name, "cpu")
        print(f"  measuring {name} ({device}) ...", end=" ", flush=True)
        row = Row(name=name, device=device, size_mb=_size_mb(path))
        try:
            model = YOLO(str(path))
            row.__dict__.update(_validate(model, device))
            row.p50_ms, row.p95_ms = _measure(model, device, images)
            print(f"mAP50 {row.map50}  p50 {row.p50_ms} ms")
        except Exception as exc:  # noqa: BLE001
            row.status = f"failed: {type(exc).__name__}"
            print(f"FAILED ({type(exc).__name__}: {exc})")
        rows.append(row)

    return rows


def render(rows: list[Row], baseline: Row | None) -> str:
    head = (
        "| Format | Device | mAP50 | ΔmAP50 | mAP50-95 | p50 ms | p95 ms | FPS | Size MB |\n"
        "|--------|--------|------:|-------:|---------:|-------:|-------:|----:|--------:|"
    )
    lines = [head]
    for r in rows:
        if r.status != "ok" or r.map50 is None:
            lines.append(f"| {r.name} | {r.device} | — | — | — | — | — | — | {r.size_mb or '—'} |")
            continue
        delta = ""
        if baseline and baseline.map50:
            d = r.map50 - baseline.map50
            delta = "baseline" if r is baseline else f"{d:+.4f}"
        lines.append(
            f"| {r.name} | {r.device} | {r.map50:.4f} | {delta} | {r.map5095:.4f} | "
            f"{r.p50_ms} | {r.p95_ms} | {r.fps} | {r.size_mb} |"
        )
    return "\n".join(lines)


JETSON_SCRIPT = '''#!/usr/bin/env python3
"""
TensorRT export and benchmark. Run this ON the Jetson — it needs CUDA.

Produces the rows export_bench.py cannot: TensorRT FP16 and INT8. Methodology is
deliberately identical (same validation split, same percentile latency, warm-up
discarded) so the numbers drop straight into the same table.

INT8 needs a calibration set. Ultralytics uses the dataset's own images, which is
correct here: calibrating on data that resembles production is the whole point,
and calibrating on random images is how INT8 quietly loses accuracy.

    python jetson_bench.py --weights best.pt --data sure_dataset.yaml
"""
import argparse, json, statistics, time
from pathlib import Path
from ultralytics import YOLO


def measure(model, images, warmup=8):
    for p in images[:warmup]:
        model.predict(p, verbose=False)
    t = []
    for p in images:
        t0 = time.perf_counter()
        model.predict(p, verbose=False)
        t.append((time.perf_counter() - t0) * 1000)
    t.sort()
    return round(statistics.median(t), 2), round(t[int(0.95 * len(t))], 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--imgsz", type=int, default=640)
    args = ap.parse_args()

    val_images = sorted((Path(args.data).parent / "val" / "images").glob("*.[jp][pn]g"))
    images = [str(p) for p in val_images[:40]]
    rows = []

    for label, kwargs in [
        ("tensorrt-fp16", dict(format="engine", half=True, imgsz=args.imgsz)),
        ("tensorrt-int8", dict(format="engine", int8=True, imgsz=args.imgsz,
                               data=args.data, fraction=1.0)),
    ]:
        print(f"exporting {label} ...", flush=True)
        engine = YOLO(args.weights).export(**kwargs)
        m = YOLO(engine)
        r = m.val(data=args.data, verbose=False, plots=False)
        p50, p95 = measure(m, images)
        rows.append(dict(name=label, map50=round(float(r.box.map50), 4),
                         map5095=round(float(r.box.map), 4), p50_ms=p50, p95_ms=p95,
                         size_mb=round(Path(engine).stat().st_size / 1048576, 1)))
        print(rows[-1])

    Path("jetson_results.json").write_text(json.dumps(rows, indent=2))
    print("\\nwrote jetson_results.json — merge into the table in README")


if __name__ == "__main__":
    main()
'''


def main() -> int:
    ap = argparse.ArgumentParser(description="Export the detector and measure each format")
    ap.add_argument("--formats", nargs="+",
                    default=["pt-mps", "pt-cpu", "onnx", "onnx-int8", "coreml", "torchscript"])
    ap.add_argument("--skip-export", action="store_true")
    ap.add_argument("--emit-jetson", action="store_true")
    ap.add_argument("--json", metavar="FILE")
    args = ap.parse_args()

    if args.emit_jetson:
        out = Path(__file__).parent / "jetson_bench.py"
        out.write_text(JETSON_SCRIPT, encoding="utf-8")
        out.chmod(0o755)
        print(f"wrote {out}")
        return 0

    if not WEIGHTS.exists():
        print(f"Weights not found: {WEIGHTS}\nFetch them from GitHub Releases first.")
        return 1

    print(f"Weights : {WEIGHTS.relative_to(REPO)}")
    print(f"Data    : {DATA.relative_to(REPO)}")
    print(f"Latency : p50/p95 over {LATENCY_IMAGES} real validation frames, "
          f"{WARMUP} warm-up runs discarded\n")

    if args.skip_export:
        produced = {}
        for fmt in args.formats:
            if fmt in ("pt-mps", "pt-cpu"):
                produced[fmt] = WEIGHTS
                continue
            guess = {"onnx": "best.onnx", "onnx-int8": "best-int8.onnx",
                     "coreml": "best.mlpackage", "torchscript": "best.torchscript"}[fmt]
            p = EXPORT_DIR / guess
            if p.exists():
                produced[fmt] = p
            else:
                print(f"  {fmt}: no existing export at {p.name}, skipped")
    else:
        print("Exporting")
        produced = export_all(args.formats)

    print("\nMeasuring")
    rows = benchmark(produced)

    baseline = next((r for r in rows if r.name == "pt-mps" and r.status == "ok"), None)
    print("\n" + render(rows, baseline))

    ok = [r for r in rows if r.status == "ok" and r.map50 is not None]
    if baseline and len(ok) > 1:
        worst = min(ok, key=lambda r: r.map50)
        fastest = min(ok, key=lambda r: r.p50_ms or 1e9)
        print(f"\nFastest         : {fastest.name} — {fastest.p50_ms} ms p50 "
              f"({fastest.fps} FPS), {fastest.map50 - baseline.map50:+.4f} mAP50 vs baseline, "
              f"{fastest.size_mb} MB")
        print(f"Worst accuracy  : {worst.name} — {worst.map50 - baseline.map50:+.4f} mAP50")
        smallest = min(ok, key=lambda r: r.size_mb or 1e9)
        print(f"Smallest        : {smallest.name} — {smallest.size_mb} MB "
              f"({(baseline.size_mb or 0) / (smallest.size_mb or 1):.1f}x smaller), "
              f"{smallest.map50 - baseline.map50:+.4f} mAP50")

    missing = [r.name for r in rows if r.status != "ok"]
    if missing:
        print(f"\nUnavailable on this machine: {', '.join(missing)}")
    print("\nTensorRT FP16/INT8 need CUDA and cannot run on Apple Silicon.")
    print("  python export_bench.py --emit-jetson    # script to produce those rows on device")

    if args.json:
        Path(args.json).write_text(json.dumps([asdict(r) for r in rows], indent=2),
                                   encoding="utf-8")
        print(f"\nJSON written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
