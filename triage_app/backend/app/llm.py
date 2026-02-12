"""Gọi LLM để triage incident từ context log."""
from __future__ import annotations

import json
import os
import re
from typing import Any

from .schemas import TriageResult

# Optional: OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


def _build_context(logs: list[dict[str, Any]], log_snippet: str | None, error_message: str | None) -> str:
    parts = ["## Logs liên quan (từ Vector DB)\n"]
    for i, log in enumerate(logs[:20], 1):
        text = log.get("text") or ""
        module = log.get("module") or ""
        operation = log.get("operation") or ""
        resp_code = log.get("resp_code") or ""
        status = log.get("status") or ""
        order_no = log.get("order_no") or ""
        parts.append(f"[{i}] order_no={order_no} module={module} operation={operation} resp_code={resp_code} status={status}")
        parts.append(text[:800])
        parts.append("")
    if log_snippet:
        parts.append("## Log snippet / mô tả từ user\n" + log_snippet)
    if error_message:
        parts.append("## Error message\n" + error_message)
    return "\n".join(parts)


def _parse_llm_output(raw: str) -> TriageResult:
    """Parse output LLM (JSON hoặc YAML-like) thành TriageResult."""
    # Thử tìm JSON block
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            data = json.loads(m.group())
            return TriageResult(
                issue_type=data.get("issue_type", data.get("issueType", "")),
                confidence=float(data.get("confidence", 0) or 0),
                root_cause=data.get("root_cause", data.get("rootCause", "")),
                evidence=data.get("evidence", []) or [],
                suggested_actions=data.get("suggested_actions", data.get("suggestedActions", [])) or [],
            )
        except (json.JSONDecodeError, TypeError):
            pass
    return TriageResult(root_cause=raw[:500] if raw else "Không phân tích được.")


async def triage_with_llm(
    logs: list[dict[str, Any]],
    log_snippet: str | None = None,
    error_message: str | None = None,
) -> tuple[TriageResult, str]:
    """
    Gửi context (logs + snippet + error) cho LLM, trả về TriageResult và raw response.
    Nếu không cấu hình OpenAI thì trả về kết quả mặc định.
    """
    context = _build_context(logs, log_snippet, error_message)
    if not context.strip():
        return TriageResult(root_cause="Không có log nào để phân tích."), ""

    if not OPENAI_API_KEY:
        # Fallback: không gọi API, trả về tóm tắt đơn giản
        summary = _summarize_logs(logs)
        return TriageResult(
            issue_type="Unknown",
            confidence=0.0,
            root_cause=summary,
            evidence=[f"Tìm thấy {len(logs)} log(s)."],
            suggested_actions=["Cấu hình OPENAI_API_KEY để dùng AI triage."],
        ), ""

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        prompt = f"""Bạn là chuyên gia triage incident hệ thống thanh toán. Dựa trên các log và thông tin dưới đây, đưa ra đánh giá ngắn gọn theo đúng JSON sau (chỉ trả về JSON, không giải thích thêm):

{{
  "issue_type": "Loại lỗi (vd: Callback Failure, Payment Timeout, ...)",
  "confidence": 0.85,
  "root_cause": "Nguyên nhân gốc rễ ngắn gọn",
  "evidence": ["Bằng chứng 1", "Bằng chứng 2"],
  "suggested_actions": ["Hành động 1", "Hành động 2"]
}}

Dữ liệu:
{context}
"""
        resp = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = (resp.choices[0].message.content or "").strip()
        return _parse_llm_output(raw), raw
    except Exception as e:
        return TriageResult(
            root_cause=f"Lỗi gọi LLM: {e}",
            evidence=[],
            suggested_actions=["Kiểm tra OPENAI_API_KEY và kết nối mạng."],
        ), str(e)


def _summarize_logs(logs: list[dict[str, Any]]) -> str:
    if not logs:
        return "Không có log."
    modules = set()
    statuses = set()
    codes = set()
    for log in logs:
        if log.get("module"):
            modules.add(log["module"])
        if log.get("status"):
            statuses.add(log["status"])
        if log.get("resp_code"):
            codes.add(log["resp_code"])
    return f"Tìm thấy {len(logs)} log(s). Module: {', '.join(modules)}. Status: {', '.join(statuses)}. RespCode: {', '.join(codes)}."
