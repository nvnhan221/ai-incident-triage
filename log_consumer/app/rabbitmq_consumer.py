"""Consume từng message từ RabbitMQ (1 message = 1 log JSON), chuẩn hóa, ghi Qdrant."""
from __future__ import annotations

import json
import logging

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from .config import settings
from .normalizer import normalize_log
from .schemas import RawLog
from .vector_store import get_client, ensure_collection, upsert_logs

logger = logging.getLogger(__name__)


async def consume_loop() -> None:
    """Kết nối RabbitMQ, consume queue INCIDENT_TRIAGE_LOGS. Mỗi message = 1 log JSON → xử lý → ghi Qdrant → ack."""
    url = (
        f"amqp://{settings.rabbitmq_username}:{settings.rabbitmq_password}"
        f"@{settings.rabbitmq_host}:{settings.rabbitmq_port}/"
    )
    connection = await aio_pika.connect_robust(url)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=settings.rabbitmq_prefetch_count)

    queue = await channel.declare_queue(
        settings.rabbitmq_queue_name,
        durable=True,
    )
    client = get_client()
    ensure_collection(client)

    logger.info(
        "RabbitMQ consumer started: queue=%s prefetch=%s",
        settings.rabbitmq_queue_name,
        settings.rabbitmq_prefetch_count,
    )

    async def on_message(message: AbstractIncomingMessage) -> None:
        try:
            body = message.body.decode("utf-8")
            raw_dict = json.loads(body)
            raw = RawLog.model_validate(raw_dict)
            norm = normalize_log(raw, payload_json=body)
            upsert_logs(client, [norm])
            await message.ack()
            logger.debug("Ingested log id=%s order_no=%s", norm.id, norm.order_no)
        except Exception as e:
            logger.warning("Skip invalid log: %s", e, exc_info=False)
            await message.nack(requeue=False)

    await queue.consume(on_message, no_ack=False)
    logger.info("Consuming from queue %s (Ctrl+C to stop)", settings.rabbitmq_queue_name)
