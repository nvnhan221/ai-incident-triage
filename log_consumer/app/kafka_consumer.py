"""Consume log messages từ Kafka, chuẩn hóa, ingest vào Qdrant."""
from __future__ import annotations

import json
import logging

from aiokafka import AIOKafkaConsumer

from .config import settings
from .normalizer import normalize_log
from .schemas import RawLog
from .vector_store import get_client, upsert_logs

logger = logging.getLogger(__name__)


async def consume_loop() -> None:
    bootstrap = settings.kafka_bootstrap_servers
    topic = settings.kafka_topic_logs
    group = settings.kafka_group_id
    batch_size = settings.ingest_batch_size

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
