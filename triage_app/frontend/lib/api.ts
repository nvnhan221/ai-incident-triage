const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export type TriageRequest = {
  order_no?: string;
  order_id?: string;
  merchant_id?: string;
  request_id?: string;
  log_snippet?: string;
  error_message?: string;
};

export type LogHit = {
  order_no?: string;
  merchant_id?: string;
  module?: string;
  operation?: string;
  resp_code?: string;
  status?: string;
  timestamp?: number;
  text?: string;
  payload?: string;
};

export type TriageResult = {
  issue_type: string;
  confidence: number;
  root_cause: string;
  evidence: string[];
  suggested_actions: string[];
};

export type SearchResponse = {
  query: Record<string, unknown>;
  hits: LogHit[];
  total: number;
};

export type TriageResponse = {
  query: Record<string, unknown>;
  logs_found: number;
  logs_preview: LogHit[];
  triage: TriageResult | null;
  raw_llm?: string;
};

export async function searchLogs(body: TriageRequest): Promise<SearchResponse> {
  const res = await fetch(`${API_URL}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail ?? res.statusText);
  return data;
}

export async function triageIncident(body: TriageRequest): Promise<TriageResponse> {
  const res = await fetch(`${API_URL}/triage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail ?? res.statusText);
  return data;
}
