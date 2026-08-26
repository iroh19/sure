#!/usr/bin/env python3
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
    print("\nwrote jetson_results.json — merge into the table in README")


if __name__ == "__main__":
    main()
