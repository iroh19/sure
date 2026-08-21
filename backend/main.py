"""
S.U.R.E. — Backend Omurgası (FastAPI)
=====================================
1. vision-service'ten ByteTrack metriklerini al      -> POST /api/vision/ingest
2. vision-service'ten annotated frame'leri al         -> POST /api/vision/frame
3. Su kalitesi sensörlerini simüle/okur (mock CSV)    -> GET  /api/sensors
4. Vision + sensör birleşik anlık durum               -> GET  /api/state
5. Recharts için zaman serisi geçmişi                 -> GET  /api/history
6. AQUA-7B refah karar motoru                         -> GET  /api/decision
7. MJPEG canlı stream                                 -> GET  /api/vision/stream
8. Son annotated frame (JPEG)                         -> GET  /api/vision/frame.jpg
9. SQLite kalıcı geçmiş (restart'ta kaybolmaz)        -> sure_history.db
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
import sqlite3
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Konfigürasyon
# --------------------------------------------------------------------------- #
SENSOR_CSV   = Path(__file__).resolve().parent.parent / "data" / "sensor_mock.csv"
DB_PATH      = Path(os.getenv("DB_PATH", str(Path(__file__).resolve().parent / "sure_history.db")))
HISTORY_MAX  = 300
SENSOR_TICK  = 2.0

LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8001")
LLM_TIMEOUT     = 30.0

SAFE = {
    "temperature_c":        (16.0, 21.0),
    "dissolved_oxygen_mgl": (6.0, 12.0),
    "ph":                   (6.5, 8.0),
    "tds_ppm":              (200.0, 450.0),
}


# --------------------------------------------------------------------------- #
# Şemalar
# --------------------------------------------------------------------------- #
class Track(BaseModel):
    id: int
    bbox: list[float]
    conf: float
    speed: float


class VisionFrame(BaseModel):
    timestamp: str
    frame_id: int
    fish_count: int
    avg_activity: float
    tracks: list[Track] = Field(default_factory=list)


class SensorReading(BaseModel):
    timestamp: str
    temperature_c: float
    dissolved_oxygen_mgl: float
    ph: float
    tds_ppm: float


class ChatRequest(BaseModel):
    message: str


# --------------------------------------------------------------------------- #
# SQLite kalıcı depolama
# --------------------------------------------------------------------------- #
def _db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def db_init() -> None:
    """Tablolar yoksa oluştur, uygulama başlangıcında bir kez çağrılır."""
    with _db_connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS sensor_history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                temperature_c        REAL,
                dissolved_oxygen_mgl REAL,
                ph                   REAL,
                tds_ppm              REAL
            );
            CREATE TABLE IF NOT EXISTS vision_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp    TEXT NOT NULL,
                frame_id     INTEGER,
                fish_count   INTEGER,
                avg_activity REAL
            );
            CREATE TABLE IF NOT EXISTS decision_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                status      TEXT,
                reasoning   TEXT,
                engine      TEXT
            );
        """)
    print(f"[db] SQLite hazır: {DB_PATH}")


def db_insert_sensor(s: "SensorReading") -> None:
    with _db_connect() as conn:
        conn.execute(
            "INSERT INTO sensor_history (timestamp, temperature_c, dissolved_oxygen_mgl, ph, tds_ppm) "
            "VALUES (?, ?, ?, ?, ?)",
            (s.timestamp, s.temperature_c, s.dissolved_oxygen_mgl, s.ph, s.tds_ppm),
        )


def db_insert_vision(v: "VisionFrame") -> None:
    with _db_connect() as conn:
        conn.execute(
            "INSERT INTO vision_history (timestamp, frame_id, fish_count, avg_activity) "
            "VALUES (?, ?, ?, ?)",
            (v.timestamp, v.frame_id, v.fish_count, v.avg_activity),
        )


def db_insert_decision(d: dict) -> None:
    with _db_connect() as conn:
        conn.execute(
            "INSERT INTO decision_history (timestamp, status, reasoning, engine) "
            "VALUES (?, ?, ?, ?)",
            (d.get("timestamp"), d.get("status"), d.get("reasoning"), d.get("engine")),
        )


def db_load_sensor_history(limit: int = HISTORY_MAX) -> list[dict]:
    with _db_connect() as conn:
        rows = conn.execute(
            "SELECT timestamp, temperature_c, dissolved_oxygen_mgl, ph, tds_ppm "
            "FROM sensor_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def db_load_vision_history(limit: int = HISTORY_MAX) -> list[dict]:
    with _db_connect() as conn:
        rows = conn.execute(
            "SELECT timestamp, frame_id, fish_count, avg_activity "
            "FROM vision_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


def db_load_decision_history(limit: int = 50) -> list[dict]:
    with _db_connect() as conn:
        rows = conn.execute(
            "SELECT timestamp, status, reasoning, engine "
            "FROM decision_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]


# --------------------------------------------------------------------------- #
# Durum deposu
# --------------------------------------------------------------------------- #
class Store:
    def __init__(self):
        self.latest_vision: Optional[VisionFrame] = None
        self.latest_sensor: Optional[SensorReading] = None
        self.vision_history: deque[VisionFrame] = deque(maxlen=HISTORY_MAX)
        self.sensor_history: deque[SensorReading] = deque(maxlen=HISTORY_MAX)
        self.latest_frame_jpeg: Optional[bytes] = None   # annotated JPEG

    def push_vision(self, v: VisionFrame):
        self.latest_vision = v
        self.vision_history.append(v)
        db_insert_vision(v)

    def push_sensor(self, s: SensorReading):
        self.latest_sensor = s
        self.sensor_history.append(s)
        db_insert_sensor(s)

    def push_frame(self, jpeg_bytes: bytes):
        self.latest_frame_jpeg = jpeg_bytes


store = Store()


# --------------------------------------------------------------------------- #
# Sensör simülatörü
# --------------------------------------------------------------------------- #
def load_sensor_rows() -> list[dict]:
    if not SENSOR_CSV.exists():
        return []
    with open(SENSOR_CSV) as f:
        return list(csv.DictReader(f))


async def sensor_loop():
    rows = load_sensor_rows()
    if not rows:
        print(f"[sensor_loop] {SENSOR_CSV} bulunamadı.")
        return
    i = 0
    while True:
        row = rows[i % len(rows)]
        store.push_sensor(SensorReading(
            timestamp=datetime.now(timezone.utc).isoformat(),
            temperature_c=float(row["temperature_c"]),
            dissolved_oxygen_mgl=float(row["dissolved_oxygen_mgl"]),
            ph=float(row["ph"]),
            tds_ppm=float(row["tds_ppm"]),
        ))
        i += 1
        await asyncio.sleep(SENSOR_TICK)


# --------------------------------------------------------------------------- #
# Kural-tabanlı fallback
# --------------------------------------------------------------------------- #
def rule_based_decision(v: Optional[VisionFrame], s: Optional[SensorReading]) -> dict:
    alerts: list[str] = []
    status = "ok"
    if s:
        for key, (lo, hi) in SAFE.items():
            val = getattr(s, key)
            if val < lo or val > hi:
                alerts.append(f"{key} aralık dışı: {val} (güvenli {lo}-{hi})")
                status = "critical" if key == "dissolved_oxygen_mgl" else \
                         ("warning" if status == "ok" else status)
    if v and v.fish_count > 0 and v.avg_activity < 0.002:
        alerts.append(f"Balık aktivitesi çok düşük ({v.avg_activity})")
        status = "warning" if status == "ok" else status
    if not alerts:
        alerts.append("Tüm parametreler güvenli aralıkta.")
    return {
        "engine": "rule-based-fallback",
        "status": status,
        "reasoning": " ".join(alerts),
        "recommendations": _recommend(status),
    }


def _recommend(status: str) -> list[str]:
    if status == "critical":
        return ["Havalandırmayı/oksijen pompasını derhal artır.", "Yemlemeyi durdur, suyu kontrol et."]
    if status == "warning":
        return ["Parametreleri yakından izle.", "Trend kötüleşirse müdahale planı hazırla."]
    return ["Mevcut bakım rutinini sürdür."]


def _snapshot(v: Optional[VisionFrame], s: Optional[SensorReading],
              with_ranges: bool = False) -> dict:
    """vision + sensor anlık görüntüsü — LLM servisine giden ortak yük.
    with_ranges=True karar motoru için güvenli aralıkları da ekler."""
    snap = {
        "vision": v.model_dump() if v else None,
        "sensor": s.model_dump() if s else None,
    }
    if with_ranges:
        snap["safe_ranges"] = SAFE
    return snap


# --------------------------------------------------------------------------- #
# AQUA-7B karar motoru
# --------------------------------------------------------------------------- #
async def aqua_llm_decision(v: Optional[VisionFrame], s: Optional[SensorReading]) -> dict:
    snapshot = _snapshot(v, s, with_ranges=True)
    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            resp = await client.post(f"{LLM_SERVICE_URL}/generate", json={"snapshot": snapshot})
            resp.raise_for_status()
            parsed = resp.json()

            # Kural motoru override — LLM kritik senaryoları ıskalasa override et
            rule = rule_based_decision(v, s)
            severity = {"ok": 0, "warning": 1, "critical": 2}
            if severity.get(rule["status"], 0) > severity.get(parsed.get("status", "ok"), 0):
                parsed["status"] = rule["status"]
                parsed["reasoning"] += f" [Kural motoru override: {rule['reasoning']}]"
                parsed.setdefault("recommendations", [])
                parsed["recommendations"] = rule["recommendations"] + parsed["recommendations"]
            return parsed
    except (httpx.HTTPError, KeyError) as exc:
        fallback = rule_based_decision(v, s)
        fallback["llm_error"] = str(exc)
        return fallback


async def aqua_chat(message: str, v: Optional[VisionFrame], s: Optional[SensorReading]) -> str:
    context = _snapshot(v, s)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{LLM_SERVICE_URL}/chat",
                                     json={"message": message, "context": context})
            resp.raise_for_status()
            return resp.json().get("reply", "").strip()
    except Exception as exc:
        rule = rule_based_decision(v, s)
        return (f"[LLM servisi erişilemez — kural motoru özeti] "
                f"Durum: {rule['status']}. {rule['reasoning']}")


# --------------------------------------------------------------------------- #
# Uygulama
# --------------------------------------------------------------------------- #
app = FastAPI(title="S.U.R.E. Backend", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def _startup():
    # SQLite tablolarını oluştur
    db_init()

    # Önceki oturumdan kalan geçmişi in-memory deque'ya yükle
    for row in db_load_sensor_history():
        try:
            store.sensor_history.append(SensorReading(**row))
        except Exception:
            pass

    for row in db_load_vision_history():
        try:
            # tracks alanı DB'de saklanmıyor — boş liste ile yükle
            store.vision_history.append(VisionFrame(tracks=[], **row))
        except Exception:
            pass

    if store.sensor_history:
        store.latest_sensor = store.sensor_history[-1]
        print(f"[startup] {len(store.sensor_history)} sensör kaydı DB'den yüklendi.")
    if store.vision_history:
        store.latest_vision = store.vision_history[-1]
        print(f"[startup] {len(store.vision_history)} vision kaydı DB'den yüklendi.")

    asyncio.create_task(sensor_loop())


@app.get("/api/health")
async def health():
    return {"status": "up", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/api/vision/ingest")
async def vision_ingest(frame: VisionFrame):
    store.push_vision(frame)
    return {"ok": True, "frame_id": frame.frame_id}


@app.post("/api/vision/frame")
async def vision_frame_ingest(request: Request):
    """vision-service'ten gelen annotated JPEG frame'i depolar."""
    body = await request.body()
    store.push_frame(body)
    return {"ok": True}


@app.get("/api/vision/frame.jpg")
async def get_latest_frame():
    """Son annotated JPEG frame'i döner (frontend polling için)."""
    if store.latest_frame_jpeg is None:
        return Response(status_code=204)
    return Response(content=store.latest_frame_jpeg, media_type="image/jpeg")


@app.get("/api/vision/stream")
async def vision_stream():
    """MJPEG stream — frontend <img src> ile doğrudan gösterilir."""
    async def generator():
        last_frame_id = -1
        while True:
            jpeg = store.latest_frame_jpeg
            if jpeg and id(jpeg) != last_frame_id:
                last_frame_id = id(jpeg)
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")
            await asyncio.sleep(0.1)   # 10 fps max

    return StreamingResponse(
        generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/api/sensors", response_model=Optional[SensorReading])
async def get_sensors():
    return store.latest_sensor


@app.get("/api/state")
async def get_state():
    return {
        "vision": store.latest_vision.model_dump() if store.latest_vision else None,
        "sensor": store.latest_sensor.model_dump() if store.latest_sensor else None,
    }


@app.get("/api/history")
async def get_history():
    return {
        "vision": [v.model_dump() for v in store.vision_history],
        "sensor": [s.model_dump() for s in store.sensor_history],
    }


@app.get("/api/decision")
async def get_decision():
    decision = await aqua_llm_decision(store.latest_vision, store.latest_sensor)
    decision["timestamp"] = datetime.now(timezone.utc).isoformat()
    db_insert_decision(decision)
    return decision


@app.get("/api/decision/history")
async def get_decision_history(limit: int = 50):
    """Son N kararı döner (SQLite'dan — restart'ta kaybolmaz)."""
    return db_load_decision_history(limit)


@app.get("/api/decision/stream")
async def get_decision_stream():
    """AQUA-7B kararını SSE olarak stream eder. Frontend EventSource ile tüketir."""
    snapshot = _snapshot(store.latest_vision, store.latest_sensor, with_ranges=True)

    async def generator():
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", f"{LLM_SERVICE_URL}/generate/stream",
                    json={"snapshot": snapshot}
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.HTTPError:
            # LLM servisi erişilemezse kural motoru fallback
            rule = rule_based_decision(store.latest_vision, store.latest_sensor)
            yield f"data: {json.dumps({'token': rule['reasoning']})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """Aqua sohbet yanıtını SSE olarak stream eder."""
    context = _snapshot(store.latest_vision, store.latest_sensor)

    async def generator():
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", f"{LLM_SERVICE_URL}/chat/stream",
                    json={"message": req.message, "context": context}
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            yield f"{line}\n\n"
        except httpx.HTTPError as exc:
            yield f"data: {json.dumps({'token': f'[Bağlantı hatası: {exc}]'})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@app.post("/api/chat")
async def chat(req: ChatRequest):
    reply = await aqua_chat(req.message, store.latest_vision, store.latest_sensor)
    return {"reply": reply, "timestamp": datetime.now(timezone.utc).isoformat()}
