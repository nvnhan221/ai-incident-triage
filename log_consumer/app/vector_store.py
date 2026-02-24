"""Ingest và query cơ bản với Qdrant."""
from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams

from .config import settings
from .schemas import NormalizedLog

VECTOR_SIZE = 1  # Dummy size khi chưa dùng embedding; filter bằng payload


def get_client() -> QdrantClient:
    return QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)


def ensure_collection(client: QdrantClient, vector_size: int = VECTOR_SIZE) -> None:
    """Tạo collection nếu chưa có. Dùng vector size 1 (dummy) nếu chỉ filter metadata."""
    from qdrant_client.http import models as rest
    try:
        client.get_collection(settings.qdrant_collection)
    except Exception:
        try:
            client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                optimizers_config=rest.OptimizersConfigDiff(default_segment_number=1),
            )
        except UnexpectedResponse as e:
            if e.status_code != 409:
                raise
        except Exception as e:
            if "already exists" not in str(e).lower() and "409" not in str(e):
                raise


def _to_point_id(record_id: str):
    """Qdrant chỉ chấp nhận point id là UUID hoặc unsigned int. Tạo UUID từ record_id (deterministic)."""
    return uuid.uuid5(uuid.NAMESPACE_OID, record_id)


def payload_to_point(norm: NormalizedLog, vector: list[float] | None = None) -> PointStruct:
    """Chuyển NormalizedLog thành PointStruct cho Qdrant."""
    if vector is None:
        vector = [0.0] * VECTOR_SIZE  # dummy vector
    point_id = _to_point_id(norm.id)
    payload: dict[str, Any] = {
        "request_id": norm.request_id,
        "order_no": norm.order_no,
        "order_id": norm.order_id,
        "trace_id": norm.trace_id,
        "merchant_id": norm.merchant_id,
        "branch_code": norm.branch_code,
        "channel": norm.channel,
        "module": norm.module,
        "operation": norm.operation,
        "resp_code": norm.resp_code,
        "status": norm.status,
        "timestamp": norm.timestamp,
        "processing_time_ms": norm.processing_time_ms,
        "text": norm.text,
        "payload": norm.payload,
    }
    if norm.amount is not None:
        payload["amount"] = norm.amount
    return PointStruct(id=str(point_id), vector=vector, payload=payload)


def upsert_logs(client: QdrantClient, normalized: list[NormalizedLog]) -> None:
    """Ghi danh sách NormalizedLog vào Qdrant."""
    if not normalized:
        return
    ensure_collection(client)
    points = [payload_to_point(n) for n in normalized]
    client.upsert(collection_name=settings.qdrant_collection, points=points)


def search_by_order_no(client: QdrantClient, order_no: str, limit: int = 50) -> list[dict[str, Any]]:
    """Tìm logs theo order_no (metadata filter)."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    ensure_collection(client)
    results = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(must=[FieldCondition(key="order_no", match=MatchValue(value=order_no))]),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [dict(payload or {}) for _, payload in results[0]]


def search_by_merchant_id(client: QdrantClient, merchant_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Tìm logs theo merchant_id."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    ensure_collection(client)
    results = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(must=[FieldCondition(key="merchant_id", match=MatchValue(value=merchant_id))]),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [dict(payload or {}) for _, payload in results[0]]


def search_by_request_id(client: QdrantClient, request_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Tìm logs theo request_id."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue
    ensure_collection(client)
    results = client.scroll(
        collection_name=settings.qdrant_collection,
        scroll_filter=Filter(must=[FieldCondition(key="request_id", match=MatchValue(value=request_id))]),
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    return [dict(payload or {}) for _, payload in results[0]]
