"""
Log Consumer Service:
- HTTP: POST /ingest nhận log (JSON), chuẩn hóa, ingest vào Vector DB (dùng test hoặc webhook).
- RabbitMQ: background task consume queue INCIDENT_TRIAGE_LOGS, chuẩn hóa, ingest.
"""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .normalizer import normalize_log
from .schemas import RawLog
from .vector_store import get_client, ensure_collection, upsert_logs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Log Consumer", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ingest")
def ingest_one(body: dict):
    """Nhận 1 log (JSON), chuẩn hóa và ingest vào Vector DB. Dùng cho test hoặc webhook."""
    try:
        raw = RawLog.model_validate(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    norm = normalize_log(raw, payload_json=json.dumps(body, ensure_ascii=False))
    client = get_client()
    ensure_collection(client)
    upsert_logs(client, [norm])
    return {"id": norm.id, "order_no": norm.order_no, "merchant_id": norm.merchant_id}


@app.post("/ingest/batch")
def ingest_batch(body: list[dict]):
    """Nhận nhiều log, chuẩn hóa và ingest."""
    normalized = []
    for item in body:
        try:
            raw = RawLog.model_validate(item)
            norm = normalize_log(raw, payload_json=json.dumps(item, ensure_ascii=False))
            normalized.append(norm)
        except Exception as e:
            logger.warning("Skip invalid log: %s", e)
    if not normalized:
        raise HTTPException(status_code=400, detail="No valid logs")
    client = get_client()
    ensure_collection(client)
    upsert_logs(client, normalized)
    return {"ingested": len(normalized), "ids": [n.id for n in normalized]}


@app.on_event("startup")
async def start_rabbitmq_consumer():
    """Chạy RabbitMQ consumer trong background nếu bật (trong .env: RABBITMQ_ENABLED=true)."""
    if settings.rabbitmq_enabled:
        from .rabbitmq_consumer import consume_loop
        asyncio.create_task(consume_loop())
        logger.info("RabbitMQ consumer task started")
    else:
        logger.info("RabbitMQ disabled; use POST /ingest or /ingest/batch to push logs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.http_port)
