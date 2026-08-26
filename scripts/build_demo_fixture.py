"""
Record a real session into a static fixture the Pages demo can replay.

GitHub Pages serves static files only — FastAPI, AQUA-1B and pgvector cannot run
there. So the published demo replays a recording instead of computing live, and
the page says so on its face. A demo that looks live but is pre-recorded, without
saying it, is a fabricated record.

Everything in the fixture is produced by the real components:

  sensors    data/sensor_mock.csv, the same file the backend replays, including
             the deliberate oxygen dip at rows 60-75
  vision     the actual YOLOv11s detector with ByteTrack over data/demo.MOV,
             using yolo_runner's own ActivityTracker — real fish counts and real
             normalised movement, not synthesised numbers
  decisions  backend/rules.py, the production rule engine
  citations  the real pgvector retrieval, when it is reachable

Model narration is optional (--with-llm) because it needs AQUA-1B loaded. Without
it the reasoning text comes from the rule engine, which is not a stand-in: it is
the documented fallback path the system takes whenever the LLM service is down.

    python scripts/build_demo_fixture.py
    python scripts/build_demo_fixture.py --with-llm --frames 120
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))
sys.path.insert(0, str(REPO / "vision-service"))
sys.path.insert(0, str(REPO / "llm-service"))

OUT = REPO / "frontend" / "public" / "demo-session.json"
SENSOR_CSV = REPO / "data" / "sensor_mock.csv"
VIDEO = REPO / "data" / "demo.MOV"
WEIGHTS = REPO / "sure_models" / "sure_v1" / "weights" / "best.pt"

# Frames discarded while ByteTrack establishes track identities.
WARMUP_FRAMES = 10


def load_sensors(limit: int) -> list[dict]:
    rows = []
    with open(SENSOR_CSV, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append({
                "timestamp": row["timestamp"],
                "temperature_c": float(row["temperature_c"]),
                "dissolved_oxygen_mgl": float(row["dissolved_oxygen_mgl"]),
                "ph": float(row["ph"]),
                "tds_ppm": float(row["tds_ppm"]),
            })
    return rows[:limit]


def run_vision(n_frames: int, device: str) -> list[dict]:
    """Real detection and tracking over the demo video."""
    import cv2
    import numpy as np
    from ultralytics import YOLO

    from yolo_runner import ActivityTracker

    if not WEIGHTS.exists():
        print(f"  weights missing ({WEIGHTS.name}) — vision channel will be empty")
        return []
    if not VIDEO.exists():
        print(f"  video missing ({VIDEO.name}) — vision channel will be empty")
        return []

    model = YOLO(str(WEIGHTS))
    activity = ActivityTracker()
    cap = cv2.VideoCapture(str(VIDEO))
    out: list[dict] = []

    # The tracker reports zero speed on a track's first appearance — there is no
    # previous centre to difference against. Keeping those frames would put a
    # genuine-looking "activity critically low" warning at the start of every
    # replay that is an artefact of a cold tracker, not an observation.
    warmup = WARMUP_FRAMES

    while len(out) < n_frames + warmup:
        ok, frame = cap.read()
        if not ok:  # loop the clip rather than pad with zeros
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = cap.read()
            if not ok:
                break

        res = model.track(frame, persist=True, tracker="bytetrack.yaml",
                          device=device, verbose=False)[0]

        speeds: list[float] = []
        active: set[int] = set()
        if res.boxes is not None and res.boxes.id is not None:
            diag = float(np.hypot(frame.shape[1], frame.shape[0]))
            for box, tid in zip(res.boxes.xyxy.tolist(), res.boxes.id.int().tolist()):
                cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
                speeds.append(activity.update(int(tid), cx, cy, diag))
                active.add(int(tid))
            activity.forget_missing(active)

        out.append({
            "frame_id": len(out),
            "fish_count": len(active),
            "avg_activity": round(float(np.mean(speeds)), 5) if speeds else 0.0,
        })
        if len(out) % 20 == 0:
            print(f"  {len(out)}/{n_frames + warmup} frames", flush=True)

    cap.release()
    out = out[warmup:]
    for i, row in enumerate(out):   # renumber so frame_id starts at 0
        row["frame_id"] = i
    return out


def decide(sensor: dict, vision: dict | None) -> dict:
    """The production rule engine, unmodified."""
    import rules

    verdict = rules.evaluate(sensor, vision)
    verdict["recommendations"] = rules.recommend(verdict["status"])
    return verdict


def citations_for(sensor: dict, vision: dict | None) -> list[dict]:
    """Real retrieval, when pgvector is reachable. Empty list otherwise."""
    try:
        from agent.router import plan
        from rag.retriever import build_context, retrieve
    except Exception:
        return []

    snapshot = {"sensor": sensor, "vision": vision or {}}
    query = next((args["query"] for name, args in plan(snapshot)
                  if name == "query_knowledge_base"), None)
    if not query:
        return []
    _, sources = build_context(retrieve(query), max_chars=900)
    return sources


def narrate(snapshot: dict) -> str | None:
    try:
        import inference

        result = inference.generate_decision(snapshot)
        return result.get("reasoning")
    except Exception as exc:  # noqa: BLE001
        print(f"  narration unavailable ({type(exc).__name__}) — using rule engine text")
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Record a session for the static demo")
    ap.add_argument("--frames", type=int, default=120)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--with-llm", action="store_true",
                    help="run AQUA-1B for each distinct status (slow, needs the model)")
    args = ap.parse_args()

    print("Sensors")
    sensors = load_sensors(args.frames)
    print(f"  {len(sensors)} readings from {SENSOR_CSV.name}")

    print("Vision — real detector with tracking")
    vision = run_vision(len(sensors), args.device)
    print(f"  {len(vision)} frames")

    print("Decisions — production rule engine")
    steps: list[dict] = []
    narration_cache: dict[str, str] = {}

    for i, sensor in enumerate(sensors):
        v = vision[i] if i < len(vision) else None
        if v:
            v = {**v, "timestamp": sensor["timestamp"]}

        verdict = decide(sensor, v)
        sources = citations_for(sensor, v)

        reasoning = verdict.get("reasoning", "")
        if args.with_llm:
            # One model call per distinct status keeps this to a few calls
            # instead of one per frame, and the text is genuine model output.
            key = verdict["status"]
            if key not in narration_cache:
                print(f"  narrating '{key}' ...", flush=True)
                text = narrate({"sensor": sensor, "vision": v})
                if text:
                    narration_cache[key] = text
            reasoning = narration_cache.get(key, reasoning)

        steps.append({
            "timestamp": sensor["timestamp"],
            "sensor": sensor,
            "vision": v,
            "decision": {
                "status": verdict["status"],
                "reasoning": reasoning,
                "recommendations": verdict.get("recommendations", []),
                "alerts": verdict.get("alerts", []),
                "engine": "aqua-1b/mlx" if args.with_llm and narration_cache else "rules",
                "timestamp": sensor["timestamp"],
                "sources": sources,
            },
        })

    statuses = {}
    for s in steps:
        statuses[s["decision"]["status"]] = statuses.get(s["decision"]["status"], 0) + 1

    fixture = {
        "meta": {
            "kind": "recorded-session",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "steps": len(steps),
            "note": (
                "Pre-recorded replay. GitHub Pages serves static files only, so no "
                "inference runs in the browser. Sensors, detections and decisions "
                "were produced by the real components; see scripts/build_demo_fixture.py."
            ),
            "provenance": {
                "sensors": "data/sensor_mock.csv (backend replays this file)",
                "vision": "YOLOv11s + ByteTrack over data/demo.MOV",
                "decisions": "backend/rules.py",
                "narration": "AQUA-1B" if narration_cache else "rule engine (LLM fallback path)",
                "citations": "pgvector retrieval" if any(s["decision"]["sources"] for s in steps)
                             else "unavailable when recorded",
            },
            "status_counts": statuses,
        },
        "steps": steps,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, ensure_ascii=False, indent=1), encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"\nWrote {OUT.relative_to(REPO)}  ({size_kb:.0f} KB, {len(steps)} steps)")
    print(f"Status distribution: {statuses}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
