"use client";

import { useState } from "react";
import { searchLogs, triageIncident } from "@/lib/api";
import type { SearchResponse, TriageResponse, LogHit, TriageResult } from "@/lib/api";

function LogItem({ h }: { h: LogHit }) {
  const meta = [h.module, h.operation, h.resp_code, h.status].filter(Boolean).join(" · ");
  return (
    <div className="rounded-lg border border-border bg-bg p-3 text-sm mb-2">
      <div className="text-accent mb-1">{meta}</div>
      <div className="text-muted break-all">{(h.text ?? "").slice(0, 300)}</div>
      {h.payload && (
        <pre className="mt-2 overflow-x-auto text-xs">{h.payload.slice(0, 500)}</pre>
      )}
    </div>
  );
}

function TriageBox({ t }: { t: TriageResult }) {
  const confidencePct = t.confidence ? Math.round(t.confidence * 100) : null;
  return (
    <div className="border-l-4 border-accent rounded-r-lg bg-bg p-4">
      <p className="mb-2">
        <span className="text-success font-semibold">{t.issue_type || "N/A"}</span>
        {confidencePct != null && (
          <span className="text-warning ml-2">({confidencePct}%)</span>
        )}
      </p>
      <p className="mb-2">
        <strong>Root cause:</strong> {t.root_cause}
      </p>
      {t.evidence?.length > 0 && (
        <p className="mb-2">
          <strong>Evidence:</strong>
          <ul className="list-disc pl-5 mt-1 space-y-1">
            {t.evidence.map((ev, i) => (
              <li key={i}>{ev}</li>
            ))}
          </ul>
        </p>
      )}
      {t.suggested_actions?.length > 0 && (
        <p>
          <strong>Suggested actions:</strong>
          <ul className="list-disc pl-5 mt-1 space-y-1">
            {t.suggested_actions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </p>
      )}
    </div>
  );
}

export default function Home() {
  const [orderNo, setOrderNo] = useState("");
  const [merchantId, setMerchantId] = useState("");
  const [requestId, setRequestId] = useState("");
  const [logSnippet, setLogSnippet] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [loading, setLoading] = useState<"search" | "triage" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResponse | null>(null);
  const [triageResult, setTriageResult] = useState<TriageResponse | null>(null);
  const [resultMode, setResultMode] = useState<"search" | "triage" | null>(null);

  const body = () => {
    const b: Record<string, string> = {};
    if (orderNo.trim()) b.order_no = orderNo.trim();
    if (merchantId.trim()) b.merchant_id = merchantId.trim();
    if (requestId.trim()) b.request_id = requestId.trim();
    if (logSnippet.trim()) b.log_snippet = logSnippet.trim();
    if (errorMessage.trim()) b.error_message = errorMessage.trim();
    return b;
  };

  const hasQuery = () => orderNo.trim() || merchantId.trim() || requestId.trim();

  const handleSearch = async () => {
    if (!hasQuery()) {
      setError("Nhập ít nhất một trong: Mã đơn hàng, Merchant ID, Request ID");
      setResultMode(null);
      return;
    }
    setError(null);
    setLoading("search");
    setTriageResult(null);
    try {
      const data = await searchLogs(body());
      setSearchResult(data);
      setResultMode("search");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi tìm kiếm");
    } finally {
      setLoading(null);
    }
  };

  const handleTriage = async () => {
    if (!hasQuery()) {
      setError("Nhập ít nhất một trong: Mã đơn hàng, Merchant ID, Request ID");
      setResultMode(null);
      return;
    }
    setError(null);
    setLoading("triage");
    setSearchResult(null);
    try {
      const data = await triageIncident(body());
      setTriageResult(data);
      setResultMode("triage");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Lỗi triage");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-1">AI Incident Triage</h1>
      <p className="text-muted text-sm mb-6">
        Nhập mã đơn / merchant / request để tìm log và gợi ý xử lý
      </p>

      <div className="rounded-xl border border-border bg-surface p-5 mb-6">
        <label className="block text-muted text-sm mb-1">Mã đơn hàng (orderNo)</label>
        <input
          type="text"
          value={orderNo}
          onChange={(e) => setOrderNo(e.target.value)}
          placeholder="vd: Y20KI9R6"
          className="w-full px-3 py-2.5 rounded-lg border border-border bg-bg text-[var(--text)] placeholder:text-muted mb-3 focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-3">
          <div>
            <label className="block text-muted text-sm mb-1">Merchant ID</label>
            <input
              type="text"
              value={merchantId}
              onChange={(e) => setMerchantId(e.target.value)}
              placeholder="vd: 9800000367"
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-bg text-[var(--text)] placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
          <div>
            <label className="block text-muted text-sm mb-1">Request ID</label>
            <input
              type="text"
              value={requestId}
              onChange={(e) => setRequestId(e.target.value)}
              placeholder="(tùy chọn)"
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-bg text-[var(--text)] placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>
        <label className="block text-muted text-sm mb-1">Log snippet / mô tả (tùy chọn)</label>
        <textarea
          value={logSnippet}
          onChange={(e) => setLogSnippet(e.target.value)}
          placeholder="Dán đoạn log hoặc mô tả sự cố..."
          rows={3}
          className="w-full px-3 py-2.5 rounded-lg border border-border bg-bg text-[var(--text)] placeholder:text-muted mb-3 resize-y focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <label className="block text-muted text-sm mb-1">Error message (tùy chọn)</label>
        <input
          type="text"
          value={errorMessage}
          onChange={(e) => setErrorMessage(e.target.value)}
          placeholder="Thông báo lỗi nếu có"
          className="w-full px-3 py-2.5 rounded-lg border border-border bg-bg text-[var(--text)] placeholder:text-muted mb-4 focus:outline-none focus:ring-2 focus:ring-accent"
        />
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleSearch}
            disabled={!!loading}
            className="px-6 py-3 rounded-lg bg-accent text-white font-medium hover:opacity-90 disabled:opacity-50"
          >
            {loading === "search" ? "Đang tìm..." : "Tìm logs"}
          </button>
          <button
            type="button"
            onClick={handleTriage}
            disabled={!!loading}
            className="px-6 py-3 rounded-lg bg-border text-[var(--text)] font-medium hover:opacity-90 disabled:opacity-50"
          >
            {loading === "triage" ? "Đang triage..." : "Triage (AI)"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-error/10 text-error p-4 mb-6">{error}</div>
      )}

      {resultMode === "search" && searchResult && (
        <div className="rounded-xl border border-border bg-surface p-5">
          <h2 className="text-muted text-sm font-medium mb-3">Tìm kiếm logs</h2>
          <p className="mb-4">
            Tìm thấy <strong>{searchResult.total}</strong> log(s).
          </p>
          <div className="space-y-2">
            {searchResult.hits.map((h, i) => (
              <LogItem key={i} h={h} />
            ))}
          </div>
        </div>
      )}

      {resultMode === "triage" && triageResult && (
        <div className="rounded-xl border border-border bg-surface p-5">
          <h2 className="text-muted text-sm font-medium mb-3">Kết quả Triage</h2>
          <p className="mb-4">
            Đã tìm thấy <strong>{triageResult.logs_found}</strong> log(s).
          </p>
          {triageResult.triage && <TriageBox t={triageResult.triage} />}
          {triageResult.logs_preview?.length > 0 && (
            <>
              <h3 className="text-muted text-sm mt-6 mb-2">Logs preview</h3>
              <div className="space-y-2">
                {triageResult.logs_preview.slice(0, 5).map((h, i) => (
                  <LogItem key={i} h={h} />
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
