"""
S.U.R.E. — Vision Service (YOLO + ByteTrack)
=============================================
Klasördeki videoları sırayla / sonsuz döngüyle işleyerek canlı yayın
taklit eder; her kare için bbox + HUD overlay çizilir ve backend'e JPEG
olarak POST edilir (/api/vision/frame).

Çalıştır:
  python yolo_runner.py                               # otomatik video klasörü
  python yolo_runner.py --source ../data/balık_videolar
  python yolo_runner.py --source ../data/demo.MOV     # tek video
  python yolo_runner.py --source 0                    # webcam
  python yolo_runner.py --source realsense            # Intel RealSense
"""
from __future__ import annotations

import argparse
import time
from collections import defaultdict, deque
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Iterator
from itertools import cycle

import cv2
import numpy as np
import requests
from ultralytics import YOLO

# --------------------------------------------------------------------------- #
# Konfigürasyon
# --------------------------------------------------------------------------- #
DEFAULT_MODEL   = str(Path(__file__).resolve().parent.parent /
                      "sure_models" / "sure_v1" / "weights" / "best.pt")
FALLBACK_MODEL  = str(Path(__file__).resolve().parent / "yolo11n.pt")
DEFAULT_VIDEOS  = str(Path(__file__).resolve().parent.parent /
                      "data" / "balık_videolar")
DEFAULT_BACKEND = "http://localhost:8000"

INGEST_PATH   = "/api/vision/ingest"
FRAME_PATH    = "/api/vision/frame"

CONF_THRESH   = 0.20    # 0.30→0.20: yoğun karelerde recall artışı (daha az kaçan balık)
IOU_THRESH    = 0.50
MAX_DET       = 1000    # varsayılan 300; kalabalık tankta kutu sınırını kaldır
POST_TIMEOUT  = 1.5
SPEED_WINDOW  = 5
FRAME_QUALITY = 75    # JPEG sıkıştırma (0-100)
FRAME_SKIP    = 2     # her N kareden 1 tanesini backend'e gönder

VIDEO_EXTS = {".mov", ".mp4", ".avi", ".mkv", ".webm"}


# --------------------------------------------------------------------------- #
# Veri sınıfları
# --------------------------------------------------------------------------- #
@dataclass
class TrackPayload:
    id: int
    bbox: list           # [x1, y1, x2, y2]
    conf: float
    speed: float


@dataclass
class FramePayload:
    timestamp: str
    frame_id: int
    fish_count: int
    avg_activity: float
    tracks: list = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Aktivite takibi
# --------------------------------------------------------------------------- #
class ActivityTracker:
    def __init__(self, window: int = SPEED_WINDOW):
        self._centers: dict[int, deque] = defaultdict(lambda: deque(maxlen=window))

    def update(self, tid: int, cx: float, cy: float, diag: float) -> float:
        hist = self._centers[tid]
        speed = 0.0
        if hist:
            px, py = hist[-1]
            speed = float(np.hypot(cx - px, cy - py) / max(diag, 1e-6))
        hist.append((cx, cy))
        return speed

    def forget_missing(self, active_ids: set[int]) -> None:
        for tid in list(self._centers):
            if tid not in active_ids:
                del self._centers[tid]


# --------------------------------------------------------------------------- #
# Backend sink
# --------------------------------------------------------------------------- #
class BackendSink:
    def __init__(self, base_url: str):
        self._base      = base_url.rstrip("/")
        self.ingest_url = self._base + INGEST_PATH
        self.frame_url  = self._base + FRAME_PATH
        self._session   = requests.Session()
        self._warned    = False

    def send(self, payload: FramePayload) -> None:
        try:
            self._session.post(self.ingest_url, json=asdict(payload),
                               timeout=POST_TIMEOUT)
        except requests.RequestException as exc:
            if not self._warned:
                print(f"[BackendSink] ingest POST başarısız: {exc}")
                self._warned = True

    def send_frame(self, jpeg_bytes: bytes) -> None:
        try:
            self._session.post(self.frame_url, data=jpeg_bytes,
                               headers={"Content-Type": "image/jpeg"},
                               timeout=POST_TIMEOUT)
        except requests.RequestException:
            pass   # frame kaybı kabul edilebilir


# --------------------------------------------------------------------------- #
# Kaynak üreticiler
# --------------------------------------------------------------------------- #
def _collect_videos(folder: str) -> list[Path]:
    p = Path(folder)
    if not p.is_dir():
        raise NotADirectoryError(f"Video klasörü bulunamadı: {folder}")
    videos = sorted(f for f in p.iterdir() if f.suffix.lower() in VIDEO_EXTS)
    if not videos:
        raise FileNotFoundError(f"{folder} içinde desteklenen video yok.")
    return videos


def _cv2_frames(cap: cv2.VideoCapture) -> Generator[np.ndarray, None, None]:
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            yield frame
    finally:
        cap.release()


def _realsense_frames() -> Generator[np.ndarray, None, None]:
    import pyrealsense2 as rs
    pipeline = rs.pipeline()
    cfg = rs.config()
    cfg.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    pipeline.start(cfg)
    try:
        while True:
            frames = pipeline.wait_for_frames()
            color = frames.get_color_frame()
            if color:
                yield np.asanyarray(color.get_data())
    finally:
        pipeline.stop()


def looping_video_source(source: str) -> Iterator[tuple[np.ndarray, str]]:
    """
    Kaynak tipine göre sonsuz kare üreticisi döndürür.
    Her kare ile birlikte o anki video adını da verir (HUD için).
    - Klasör → içindeki videolar sırayla, bitince baştan (cycle)
    - Tek dosya → aynı video sonsuz döner
    - Webcam indeksi → canlı akış
    - 'realsense' → RealSense akışı
    """
    if source == "realsense":
        for frame in _realsense_frames():
            yield frame, "RealSense"
        return

    if source.isdigit():
        while True:
            cap = cv2.VideoCapture(int(source))
            for frame in _cv2_frames(cap):
                yield frame, f"Webcam {source}"
        return

    p = Path(source)
    if p.is_dir():
        videos = _collect_videos(source)
        print(f"[source] {len(videos)} video bulundu, sonsuz döngüde oynatılıyor:")
        for v in videos:
            print(f"         {v.name}")
        for video_path in cycle(videos):
            print(f"\n[source] ▶ {video_path.name}")
            cap = cv2.VideoCapture(str(video_path))
            for frame in _cv2_frames(cap):
                yield frame, video_path.name
    elif p.exists():
        # Tek video dosyası — sonsuz döngü
        print(f"[source] Tek video sonsuz döngüde: {p.name}")
        while True:
            cap = cv2.VideoCapture(str(p))
            for frame in _cv2_frames(cap):
                yield frame, p.name
    else:
        raise FileNotFoundError(f"Kaynak bulunamadı: {source}")


# --------------------------------------------------------------------------- #
# HUD overlay
# --------------------------------------------------------------------------- #
def _draw_hud(frame: np.ndarray, payload: FramePayload, video_name: str) -> None:
    h, w = frame.shape[:2]
    now  = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    # Üst sol panel
    cv2.rectangle(frame, (6, 6), (250, 68), (0, 0, 0), -1)
    cv2.rectangle(frame, (6, 6), (250, 68), (0, 200, 80), 1)
    cv2.putText(frame, "S.U.R.E.  LIVE",
                (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 100), 1, cv2.LINE_AA)
    cv2.putText(frame, f"FISH: {payload.fish_count}   ACT: {payload.avg_activity:.4f}",
                (12, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 220, 255), 1, cv2.LINE_AA)
    cv2.putText(frame, video_name[:30],
                (12, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (80, 130, 80), 1, cv2.LINE_AA)

    # Sağ alt: zaman
    cv2.putText(frame, now,
                (w - 158, h - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (80, 80, 80), 1, cv2.LINE_AA)

    # Kayıt noktası (kırmızı)
    cv2.circle(frame, (w - 18, 18), 6, (0, 0, 220), -1)


# --------------------------------------------------------------------------- #
# Ana döngü
# --------------------------------------------------------------------------- #
def run(model_path: str, source: str, backend: str, device: str, show: bool) -> None:
    if not Path(model_path).exists():
        if Path(FALLBACK_MODEL).exists():
            print(f"[run] Özel model bulunamadı, fallback: {FALLBACK_MODEL}")
            model_path = FALLBACK_MODEL
        else:
            raise FileNotFoundError(f"Model yok: {model_path}")

    print(f"[run] Model  : {model_path}")
    print(f"[run] Kaynak : {source}")
    print(f"[run] Backend: {backend}")
    print(f"[run] Cihaz  : {device}\n")

    model    = YOLO(model_path)
    sink     = BackendSink(backend)
    activity = ActivityTracker()
    frame_id = 0

    for frame, video_name in looping_video_source(source):
        frame_id += 1
        h, w = frame.shape[:2]
        diag = float(np.hypot(w, h))

        results = model.track(
            frame,
            persist=True,
            tracker="bytetrack.yaml",
            conf=CONF_THRESH,
            iou=IOU_THRESH,
            max_det=MAX_DET,
            device=device,
            verbose=False,
        )

        boxes = results[0].boxes
        tracks: list[TrackPayload] = []
        active_ids: set[int] = set()

        if boxes is not None and boxes.id is not None:
            xyxy = boxes.xyxy.cpu().numpy()
            ids  = boxes.id.int().cpu().numpy()
            conf = boxes.conf.cpu().numpy()

            for (x1, y1, x2, y2), tid, c in zip(xyxy, ids, conf):
                tid = int(tid)
                active_ids.add(tid)
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                speed = activity.update(tid, cx, cy, diag)
                tracks.append(TrackPayload(
                    id=tid,
                    bbox=[float(x1), float(y1), float(x2), float(y2)],
                    conf=float(c),
                    speed=round(speed, 5),
                ))

        activity.forget_missing(active_ids)

        avg_activity = round(float(np.mean([t.speed for t in tracks])), 5) if tracks else 0.0
        payload = FramePayload(
            timestamp=datetime.now(timezone.utc).isoformat(),
            frame_id=frame_id,
            fish_count=len(active_ids),
            avg_activity=avg_activity,
            tracks=[asdict(t) for t in tracks],
        )
        sink.send(payload)

        # Annotated frame'i backend'e gönder
        if frame_id % FRAME_SKIP == 0:
            annotated = results[0].plot()
            _draw_hud(annotated, payload, video_name)
            ok, buf = cv2.imencode(".jpg", annotated,
                                   [cv2.IMWRITE_JPEG_QUALITY, FRAME_QUALITY])
            if ok:
                sink.send_frame(buf.tobytes())

        if frame_id % 30 == 0:
            print(f"  [{video_name[:20]:20s}] kare {frame_id:>6} | "
                  f"balık: {payload.fish_count:>2} | ort.aktivite: {avg_activity:.4f}")

        if show:
            cv2.imshow("S.U.R.E. Vision", results[0].plot())
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    if show:
        cv2.destroyAllWindows()


# --------------------------------------------------------------------------- #
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="S.U.R.E. YOLOv11 + ByteTrack loop runner")
    p.add_argument("--source",  default=DEFAULT_VIDEOS,
                   help="Klasör yolu, tek video, webcam indeksi (0) veya 'realsense'")
    p.add_argument("--model",   default=DEFAULT_MODEL)
    p.add_argument("--backend", default=DEFAULT_BACKEND)
    p.add_argument("--device",  default="mps", help="mps | cuda | cpu")
    p.add_argument("--show",    action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    run(a.model, a.source, a.backend, a.device, a.show)
