"""Chuẩn hóa log gốc thành NormalizedLog."""
from __future__ import annotations

import json
import re
from typing import Any

from .schemas import NormalizedLog, RawLog


def _get(data: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        v = data.get(key)
        if v is not None and str(v).strip():
            return str(v).strip()
    return default


def _get_num(data: dict[str, Any], *keys: str):
    for key in keys:
        v = data.get(key)
        if v is not None:
            try:
                return float(v) if isinstance(v, (int, float)) else float(v)
            except (TypeError, ValueError):
                pass
    return None


def _safe_json(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return str(obj)


def build_text_for_embedding(module: str, operation: str, data: dict[str, Any]) -> str:
    """Tạo chuỗi text từ log để dùng cho embedding hoặc full-text search."""
    parts = [
        f"module={module}",
        f"operation={operation}",
        f"orderNo={_get(data, 'orderNo', 'order_no')}",
        f"orderId={_get(data, 'orderId')}",
        f"traceId={_get(data, 'traceId')}",
        f"requestId={_get(data, 'requestId')}",
        f"merchantId={_get(data, 'merchantId', 'merchant_id')}",
        f"branchCode={_get(data, 'branchCode', 'branch_code')}",
        f"channel={_get(data, 'channel')}",
        f"status={_get(data, 'status')}",
        f"respCode={_get(data, 'respCode', 'responseCode')}",
    ]
    amount = _get_num(data, "amount", "paidAmount")
    if amount is not None:
        parts.append(f"amount={amount}")
    # Trích đoạn responseMessage nếu có (thường chứa thông tin lỗi)
    msg = _get(data, "responseMessage")
    if msg:
        msg_clean = re.sub(r"\s+", " ", msg)[:500]
        parts.append(f"response={msg_clean}")
    return " ".join(parts)


def normalize_log(raw: RawLog | dict[str, Any], payload_json: str | None = None) -> NormalizedLog:
    """Chuyển log gốc thành NormalizedLog."""
    if isinstance(raw, dict):
        raw = RawLog.model_validate(raw)
    data = raw.data or {}
    if not isinstance(data, dict):
        data = data.model_dump() if hasattr(data, "model_dump") else {}

    request_id = raw.requestId or _get(data, "requestId") or ""
    order_no = _get(data, "orderNo", "order_no")
    order_id = _get(data, "orderId") or ""
    trace_id = _get(data, "traceId") or ""
    merchant_id = _get(data, "merchantId", "merchant_id") or ""
    branch_code = _get(data, "branchCode", "branch_code") or ""
    amount = _get_num(data, "amount", "paidAmount")
    channel = _get(data, "channel") or ""
    status = _get(data, "status") or ""
    resp_code = raw.respCode or _get(data, "respCode", "responseCode", "errorCode") or ""

    record_id = f"{request_id}_{raw.startTime}" if request_id else f"log_{raw.startTime}"
    # Sanitize id cho Qdrant (thường dùng UUID hoặc string không có ký tự đặc biệt)
    record_id = re.sub(r"[^a-zA-Z0-9_\-.]", "_", record_id)[:128]

    text = build_text_for_embedding(raw.module, raw.operation, data)
    payload = payload_json or _safe_json(raw.model_dump(mode="json"))

    return NormalizedLog(
        id=record_id,
        request_id=request_id,
        order_no=order_no,
        order_id=order_id,
        trace_id=trace_id,
        merchant_id=merchant_id,
        branch_code=branch_code,
        amount=amount,
        channel=channel,
        module=raw.module,
        operation=raw.operation,
        resp_code=resp_code,
        status=status,
        timestamp=raw.startTime,
        processing_time_ms=raw.processingTime,
        text=text,
        payload=payload,
    )
