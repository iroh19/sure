"""
S.U.R.E. — Backend Omurgası (FastAPI)
=====================================
1. vision-service'ten ByteTrack metriklerini al      -> POST /api/vision/ingest
2. vision-service'ten annotated frame'leri al         -> POST /api/vision/frame
3. Su kalitesi sensörlerini simüle/okur (mock CSV)    -> GET  /api/sensors
4. Vision + sensör birleşik anlık durum               -> GET  /api/state
5. Recharts için zaman serisi geçmişi                 -> GET  /api/history
6. AQUA-1B refah karar motoru                         -> GET  /api/decision
7. MJPEG canlı stream                                 -> GET  /api/vision/stream
8. Son annotated frame (JPEG)                         -> GET  /api/vision/frame.jpg
9. SQLite kalıcı geçmiş (restart'ta kaybolmaz)        -> sure_history.db
"""
from __future__ import annotations

import asyncio
import csv
import json
import os
import re
import sqlite3
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
import rules
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

# Vision ~15fps gelir; her frame'i diske yazmak event loop'u bloklar.
# Canlı veri zaten Store.deque'da (maxlen=300), DB sadece trend geçmişi için.
VISION_DB_INTERVAL = float(os.getenv("VISION_DB_INTERVAL", "1.0"))   # saniye
DB_ROW_CAP         = int(os.getenv("DB_ROW_CAP", "10000"))           # tablo başına
DB_PRUNE_EVERY     = 500                                             # N yazmada bir
MAX_FRAME_BYTES    = int(os.getenv("MAX_FRAME_BYTES", str(8 * 1024 * 1024)))

# CORS: demo kapalı ağda "*" ile çalışır; production'da CORS_ORIGINS ile kısıtla.
#   örn. CORS_ORIGINS="http://localhost:5173,https://sure.example.com"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]

# Kural motoru tek kaynaktan gelir (backend/rules.py). llm-service/eval.py de
# aynı modülü import eder — eval'in ölçtüğü motor sahadaki motor olsun diye.
SAFE = rules.SAFE
SEVERITY = rules.SEVERITY
_recommend = rules.recommend


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
# Tek modül-düzeyi bağlantı. Eskiden her yazma yeni bağlantı açıyordu ve
# `with sqlite3.connect(...)` bağlantıyı KAPATMAZ (sadece commit eder) —
# ~15fps ingest altında file descriptor birikiyordu.
_db_conn: Optional[sqlite3.Connection] = None
_db_lock = threading.Lock()
_db_writes = 0


def _db() -> sqlite3.Connection:
    """Paylaşılan SQLite bağlantısı (tembel açılır)."""
    global _db_conn
    if _db_conn is None:
        _db_conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _db_conn.row_factory = sqlite3.Row
        _db_conn.execute("PRAGMA journal_mode=WAL")    # eşzamanlı okuma/yazma
        _db_conn.execute("PRAGMA synchronous=NORMAL")  # demo için fsync maliyetini düşür
    return _db_conn


def db_close() -> None:
    """Bağlantıyı kapat (uygulama kapanışında)."""
    global _db_conn
    with _db_lock:
        if _db_conn is not None:
            _db_conn.commit()
            _db_conn.close()
            _db_conn = None


def _db_write(sql: str, params: tuple) -> None:
    """Tek yazma + periyodik prune. Tüm yazmalar tek kilitten geçer."""
    global _db_writes
    with _db_lock:
        conn = _db()
        conn.execute(sql, params)
        conn.commit()
        _db_writes += 1
        if _db_writes % DB_PRUNE_EVERY == 0:
            _db_prune_locked(conn)


def _db_prune_locked(conn: sqlite3.Connection) -> None:
    """Her tabloyu son DB_ROW_CAP satıra indir. Kilit çağıran tarafından tutulur."""
    for table in ("sensor_history", "vision_history", "decision_history"):
        conn.execute(
            f"DELETE FROM {table} WHERE id <= "
            f"(SELECT MAX(id) FROM {table}) - ?", (DB_ROW_CAP,)
        )
    conn.commit()


def db_init() -> None:
    """Tablolar yoksa oluştur, uygulama başlangıcında bir kez çağrılır."""
    with _db_lock:
        conn = _db()
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
        conn.commit()
    print(f"[db] SQLite hazır: {DB_PATH}")


def db_insert_sensor(s: "SensorReading") -> None:
    _db_write(
        "INSERT INTO sensor_history (timestamp, temperature_c, dissolved_oxygen_mgl, ph, tds_ppm) "
        "VALUES (?, ?, ?, ?, ?)",
        (s.timestamp, s.temperature_c, s.dissolved_oxygen_mgl, s.ph, s.tds_ppm),
    )


def db_insert_vision(v: "VisionFrame") -> None:
    _db_write(
        "INSERT INTO vision_history (timestamp, frame_id, fish_count, avg_activity) "
        "VALUES (?, ?, ?, ?)",
        (v.timestamp, v.frame_id, v.fish_count, v.avg_activity),
    )


def db_insert_decision(d: dict) -> None:
    _db_write(
        "INSERT INTO decision_history (timestamp, status, reasoning, engine) "
        "VALUES (?, ?, ?, ?)",
        (d.get("timestamp"), d.get("status"), d.get("reasoning"), d.get("engine")),
    )


def _db_read(sql: str, params: tuple) -> list[dict]:
    with _db_lock:
        rows = _db().execute(sql, params).fetchall()
    return [dict(r) for r in reversed(rows)]


def db_load_sensor_history(limit: int = HISTORY_MAX) -> list[dict]:
    return _db_read(
        "SELECT timestamp, temperature_c, dissolved_oxygen_mgl, ph, tds_ppm "
        "FROM sensor_history ORDER BY id DESC LIMIT ?", (limit,)
    )


def db_load_vision_history(limit: int = HISTORY_MAX) -> list[dict]:
    return _db_read(
        "SELECT timestamp, frame_id, fish_count, avg_activity "
        "FROM vision_history ORDER BY id DESC LIMIT ?", (limit,)
    )


def db_load_decision_history(limit: int = 50) -> list[dict]:
    return _db_read(
        "SELECT timestamp, status, reasoning, engine "
        "FROM decision_history ORDER BY id DESC LIMIT ?", (limit,)
    )


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
        # Monotonik frame sayacı. `id(jpeg)` ile dedup yapmak güvenli değildi:
        # CPython bir nesne çöpe gidince aynı id'yi yeniden kullanabilir, o
        # yüzden yeni bir frame eski bir id'ye çakışıp atlanabiliyordu.
        self.frame_seq: int = 0
        self._last_vision_db_write: float = 0.0

    def push_vision(self, v: VisionFrame):
        self.latest_vision = v
        self.vision_history.append(v)
        # Diske ~1Hz yaz; canlı veri zaten deque'da.
        now = time.monotonic()
        if now - self._last_vision_db_write >= VISION_DB_INTERVAL:
            self._last_vision_db_write = now
            db_insert_vision(v)

    def push_sensor(self, s: SensorReading):
        self.latest_sensor = s
        self.sensor_history.append(s)
        db_insert_sensor(s)

    def push_frame(self, jpeg_bytes: bytes):
        self.latest_frame_jpeg = jpeg_bytes
        self.frame_seq += 1


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
    """Pydantic modellerini düz dict'e çevirip paylaşılan motora verir."""
    out = rules.evaluate(
        s.model_dump() if s is not None else None,
        v.model_dump() if v is not None else None,
    )
    out["engine"] = "rule-based-fallback"
    return out


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
# AQUA-1B karar motoru
# --------------------------------------------------------------------------- #
def apply_rule_override(parsed: dict, v: Optional[VisionFrame],
                        s: Optional[SensorReading]) -> dict:
    """LLM kararını kural motoruyla karşılaştır; kural daha ciddiyse yükselt.

    Bu, sistemin güvenlik ağı: model DO<6 gibi kritik bir senaryoyu ıskalarsa
    ekranda sessizce 'ok' görünmemeli. Hem /api/decision hem
    /api/decision/stream buradan geçer — iki yolun ayrışmaması için tek kaynak.
    Bilinmeyen/eksik status 0 (=ok) sayılır, yani override tarafa çalışır.
    """
    rule = rule_based_decision(v, s)
    if SEVERITY.get(rule["status"], 0) > SEVERITY.get(parsed.get("status"), 0):
        parsed["status"] = rule["status"]
        parsed["reasoning"] = (
            (parsed.get("reasoning") or "").strip()
            + f" [Kural motoru override: {rule['reasoning']}]"
        ).strip()
        parsed["recommendations"] = (
            rule["recommendations"] + list(parsed.get("recommendations") or [])
        )
        parsed["rule_override"] = True
    return parsed


def parse_decision_text(raw: str) -> dict:
    """Stream'den biriken ham metinden karar JSON'unu çıkar.

    Ayrıştırılamazsa status 'ok' varsayılır; apply_rule_override zaten
    kural motoru daha ciddiyse yukarı çeker, yani güvenli taraf korunur.
    """
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group())
            if isinstance(parsed, dict):
                parsed.setdefault("engine", "aqua-1b/stream")
                return parsed
        except json.JSONDecodeError:
            pass
    return {
        "engine": "aqua-1b/stream",
        "status": "ok",
        "reasoning": raw.strip()[:500],
        "recommendations": [],
    }


async def aqua_llm_decision(v: Optional[VisionFrame], s: Optional[SensorReading]) -> dict:
    snapshot = _snapshot(v, s, with_ranges=True)
    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            resp = await client.post(f"{LLM_SERVICE_URL}/generate", json={"snapshot": snapshot})
            resp.raise_for_status()
            parsed = resp.json()
            if not isinstance(parsed, dict):
                raise ValueError("LLM servisi sözlük döndürmedi")
            return apply_rule_override(parsed, v, s)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
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
    except (httpx.HTTPError, ValueError, KeyError):
        rule = rule_based_decision(v, s)
        return (f"[LLM servisi erişilemez — kural motoru özeti] "
                f"Durum: {rule['status']}. {rule['reasoning']}")


# --------------------------------------------------------------------------- #
# Uygulama
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Başlangıç: DB + geçmiş yükleme + sensör döngüsü. Kapanış: temiz kapat."""
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

    task = asyncio.create_task(sensor_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        db_close()
        print("[shutdown] sensör döngüsü durdu, SQLite kapatıldı.")


app = FastAPI(title="S.U.R.E. Backend", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
if CORS_ORIGINS == ["*"]:
    print("[cors] allow_origins=* (kapalı ağ demosu). "
          "Production'da CORS_ORIGINS ortam değişkenini ayarla.")


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
    if len(body) > MAX_FRAME_BYTES:
        return Response(status_code=413,
                        content=f"frame {len(body)}B > {MAX_FRAME_BYTES}B")
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
        last_seq = -1
        while True:
            seq = store.frame_seq
            jpeg = store.latest_frame_jpeg
            if jpeg and seq != last_seq:
                last_seq = seq
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
    """AQUA-1B kararını SSE olarak stream eder.

    Token'lar geldikçe `{"token": "..."}` olarak akar; sonda TEK yetkili olay
    `{"final": {...}}` gelir. İstemci status'ü DAİMA `final`den okumalı:
    kural motoru override'ı (DO<6 → critical) orada uygulanır ve karar
    decision_history'ye orada yazılır.
    """
    v, s = store.latest_vision, store.latest_sensor
    snapshot = _snapshot(v, s, with_ranges=True)

    async def generator():
        buffer = ""
        got_tokens = False
        decision: Optional[dict] = None
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", f"{LLM_SERVICE_URL}/generate/stream",
                    json={"snapshot": snapshot}
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:].strip()
                        if payload == "[DONE]":
                            break
                        try:
                            buffer += json.loads(payload).get("token", "")
                            got_tokens = True
                        except (json.JSONDecodeError, AttributeError):
                            pass
                        yield f"{line}\n\n"
        except httpx.HTTPError as exc:
            # LLM servisi erişilemezse kural motoru fallback
            decision = rule_based_decision(v, s)
            decision["llm_error"] = str(exc)
            yield f"data: {json.dumps({'token': decision['reasoning']}, ensure_ascii=False)}\n\n"

        if decision is None:
            decision = parse_decision_text(buffer) if got_tokens else rule_based_decision(v, s)
            decision = apply_rule_override(decision, v, s)

        decision["timestamp"] = datetime.now(timezone.utc).isoformat()
        db_insert_decision(decision)
        yield f"data: {json.dumps({'final': decision}, ensure_ascii=False)}\n\n"
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
