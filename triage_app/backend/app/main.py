"""
Triage Backend:
- POST /search — query Vector DB theo order_no, merchant_id, request_id; trả danh sách logs.
- POST /triage — query Vector DB + gọi LLM → trả kết quả triage (issue_type, root_cause, evidence, suggested_actions).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .schemas import TriageRequest, SearchResponse, TriageResponse, LogHit
from .vector_client import search_logs
from .llm import triage_with_llm

app = FastAPI(title="Triage API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Serve frontend static (optional): frontend/ or frontend/dist
_frontend = Path(__file__).resolve().parent.parent / "frontend"
if (_frontend / "index.html").exists():
    app.mount("/app", StaticFiles(directory=str(_frontend), html=True), name="static")
elif (_frontend / "dist" / "index.html").exists():
    app.mount("/app", StaticFiles(directory=str(_frontend / "dist"), html=True), name="static")


def _to_log_hit(p: dict) -> LogHit:
    return LogHit(
        order_no=p.get("order_no"),
        merchant_id=p.get("merchant_id"),
        module=p.get("module"),
        operation=p.get("operation"),
        resp_code=p.get("resp_code"),
        status=p.get("status"),
        timestamp=p.get("timestamp"),
        text=(p.get("text") or "")[:500],
        payload=(p.get("payload") or "")[:2000],
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    """Redirect to UI."""
    if (_frontend / "index.html").exists():
        return RedirectResponse(url="/app/")
    return {"service": "Triage API", "docs": "/docs", "search": "POST /search", "triage": "POST /triage"}


@app.post("/search", response_model=SearchResponse)
def search(req: TriageRequest):
    """Tìm logs từ Vector DB theo order_no, merchant_id, request_id."""
    if not any([req.order_no, req.merchant_id, req.request_id]):
        raise HTTPException(status_code=400, detail="Cần ít nhất một trong: order_no, merchant_id, request_id")
    hits = search_logs(order_no=req.order_no, merchant_id=req.merchant_id, request_id=req.request_id)
    return SearchResponse(
        query=req.model_dump(exclude_none=True),
        hits=[_to_log_hit(p) for p in hits],
        total=len(hits),
    )


@app.post("/triage", response_model=TriageResponse)
async def triage(req: TriageRequest):
    """Query Vector DB lấy logs → gọi LLM triage → trả kết quả."""
    if not any([req.order_no, req.merchant_id, req.request_id]):
        raise HTTPException(status_code=400, detail="Cần ít nhất một trong: order_no, merchant_id, request_id")
    hits = search_logs(order_no=req.order_no, merchant_id=req.merchant_id, request_id=req.request_id)
    triage_result, raw_llm = await triage_with_llm(
        hits,
        log_snippet=req.log_snippet,
        error_message=req.error_message,
    )
    return TriageResponse(
        query=req.model_dump(exclude_none=True),
        logs_found=len(hits),
        logs_preview=[_to_log_hit(p) for p in hits[:10]],
        triage=triage_result,
        raw_llm=raw_llm or None,
    )
