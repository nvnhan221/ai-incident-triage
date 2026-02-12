"""Consume log messages từ Kafka, chuẩn hóa, ingest vào Qdrant."""
from __future__ import annotations

import json
import logging
import os

from aiokafka import AIOKafkaConsumer

from .normalizer import normalize_log
from .schemas import RawLog
from .vector_store import get_client, upsert_logs

logger = logging.getLogger(__name__)


async def consume_loop() -> None:
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.environ.get("KAFKA_TOPIC_LOGS", "payment-logs")
    group = os.environ.get("KAFKA_GROUP_ID", "log-consumer-vector")
    batch_size = int(os.environ.get("INGEST_BATCH_SIZE", "10"))

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        group_id=group,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
    )
    await consumer.start()
    logger.info("Kafka consumer started: topic=%s group=%s", topic, group)

    batch: list = []
    client = get_client()

    try:
        async for msg in consumer:
            try:
                raw = RawLog.model_validate(msg.value)
                norm = normalize_log(raw, payload_json=json.dumps(msg.value, ensure_ascii=False))
                batch.append(norm)
            except Exception as e:
                logger.warning("Skip invalid log: %s", e, exc_info=False)
                continue

            if len(batch) >= batch_size:
                try:
                    upsert_logs(client, batch)
                    logger.info("Ingested batch size=%s", len(batch))
                except Exception as e:
                    logger.exception("Ingest failed: %s", e)
                batch = []
    finally:
        if batch:
            try:
                upsert_logs(client, batch)
            except Exception as e:
                logger.exception("Final ingest failed: %s", e)
        await consumer.stop()
