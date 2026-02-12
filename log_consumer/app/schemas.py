"""Schema log gốc và bản ghi chuẩn hóa cho Vector DB."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RawLogData(BaseModel):
    """Trường `data` trong log (một phần, các field hay dùng)."""
    orderNo: str | None = None
    orderId: str | None = None
    traceId: str | None = None
    requestId: str | None = None
    merchantId: str | None = None
    branchCode: str | None = None
    amount: int | float | None = None
    channel: str | None = None
    status: str | None = None
    date: str | None = None
    rawData: str | None = None
    responseMessage: str | None = None

    class Config:
        extra = "allow"


class RawLog(BaseModel):
    """Log gốc nhận từ Kafka (hoặc HTTP)."""
    startTime: int
    module: str = ""
    operation: str = ""
    requesterCode: str | None = None
    spanId: str | None = None
    requestId: str | None = None
    respCode: str = ""
    data: dict[str, Any] | RawLogData | None = None
    endTime: int | None = None
    processingTime: int | None = None

    class Config:
        extra = "allow"


class NormalizedLog(BaseModel):
    """Bản ghi đã chuẩn hóa để lưu Vector DB."""
    id: str
    request_id: str = ""
    order_no: str = ""
    order_id: str = ""
    trace_id: str = ""
    merchant_id: str = ""
    branch_code: str = ""
    amount: float | None = None
    channel: str = ""
    module: str = ""
    operation: str = ""
    resp_code: str = ""
    status: str = ""
    timestamp: int = 0
    processing_time_ms: int | None = None
    text: str = ""  # Dùng cho full-text hoặc embedding
    payload: str = ""  # JSON string log gốc
