from pydantic import BaseModel, Field


class TriageRequest(BaseModel):
    order_no: str | None = Field(None, description="Mã đơn hàng (vd: Y20KI9R6)")
    order_id: str | None = None
    merchant_id: str | None = Field(None, description="Mã merchant")
    request_id: str | None = None
    log_snippet: str | None = Field(None, description="Đoạn log hoặc mô tả lỗi")
    error_message: str | None = None


class TriageResult(BaseModel):
    issue_type: str = ""
    confidence: float = 0.0
    root_cause: str = ""
    evidence: list[str] = []
    suggested_actions: list[str] = []


class LogHit(BaseModel):
    order_no: str | None = None
    merchant_id: str | None = None
    module: str | None = None
    operation: str | None = None
    resp_code: str | None = None
    status: str | None = None
    timestamp: int | None = None
    text: str | None = None
    payload: str | None = None


class SearchResponse(BaseModel):
    query: dict
    hits: list[LogHit] = []
    total: int = 0


class TriageResponse(BaseModel):
    query: dict
    logs_found: int = 0
    logs_preview: list[LogHit] = []
    triage: TriageResult | None = None
    raw_llm: str | None = None
