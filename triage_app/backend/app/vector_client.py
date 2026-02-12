"""Query Vector DB (Qdrant) từ Triage BE."""
from __future__ import annotations

import os
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

COLLECTION = os.environ.get("QDRANT_COLLECTION", "payment_logs")


def get_client() -> QdrantClient:
    host = os.environ.get("QDRANT_HOST", "localhost")
    port = int(os.environ.get("QDRANT_PORT", "6333"))
    return QdrantClient(host=host, port=port)


def _scroll_filter(client: QdrantClient, must: list) -> list[dict[str, Any]]:
    try:
        results, _ = client.scroll(
            collection_name=COLLECTION,
            scroll_filter=Filter(must=must) if must else None,
            limit=100,
            with_payload=True,
            with_vectors=False,
        )
        return [dict(p.payload or {}) for p in results]
    except Exception:
        return []


def search_logs(
    order_no: str | None = None,
    merchant_id: str | None = None,
    request_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Tìm logs theo order_no, merchant_id hoặc request_id."""
    client = get_client()
    conditions = []
    if order_no:
        conditions.append(FieldCondition(key="order_no", match=MatchValue(value=order_no)))
    if merchant_id:
        conditions.append(FieldCondition(key="merchant_id", match=MatchValue(value=merchant_id)))
    if request_id:
        conditions.append(FieldCondition(key="request_id", match=MatchValue(value=request_id)))
    if not conditions:
        return []
    return _scroll_filter(client, conditions)[:limit]
