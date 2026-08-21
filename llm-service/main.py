"""
S.U.R.E. LLM Service (AQUA-7B)
================================
FastAPI servisi — backend'den gelen anlık veriyle refah kararı üretir.

Endpoint'ler:
  POST /generate   — { snapshot: {...} }  → karar JSON'u
  POST /chat       — { message, context } → serbest metin yanıt
  GET  /health
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime, timezone
import json as _json
import inference

app = FastAPI(title="S.U.R.E. LLM Service", version="1.0.0")


class DecisionRequest(BaseModel):
    snapshot: dict


class ChatRequest(BaseModel):
    message: str
    context: dict = {}


@app.on_event("startup")
async def _preload():
    # Model cold-start'ı uzun sürer; startup'ta yükle
    import asyncio, concurrent.futures
    loop = asyncio.get_event_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    await loop.run_in_executor(executor, inference._load)


@app.get("/health")
def health():
    return {"status": "up", "time": datetime.now(timezone.utc).isoformat()}


@app.post("/generate")
def generate(req: DecisionRequest):
    result = inference.generate_decision(req.snapshot)
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    return result


@app.post("/chat")
def chat(req: ChatRequest):
    reply = inference.generate_chat(req.message, req.context)
    return {"reply": reply, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/generate/stream")
def generate_stream(req: DecisionRequest):
    """SSE stream — her token ayrı `data:` satırı, bitis `data: [DONE]`."""
    def event_stream():
        for token in inference.generate_decision_stream(req.snapshot):
            yield f"data: {_json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """SSE stream for chat."""
    def event_stream():
        for token in inference.generate_chat_stream(req.message, req.context):
            yield f"data: {_json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")
