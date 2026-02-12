# Kế hoạch triển khai AI Incident Triage Engine

## 1. Tổng quan mục tiêu

- **Input:** `transactionId` / `orderId`, `merchantId`, log snippet, error message
- **Output:** Issue type, confidence %, root cause, evidence, suggested actions (YAML/structured)
- **Mục tiêu:** Giảm thời gian xử lý từ 30–120 phút xuống 2–3 phút

---

## 2. Công nghệ đề xuất

### 2.1 Backend & API

| Thành phần | Công nghệ | Lý do |
|------------|-----------|--------|
| Runtime | **Python 3.11+** | Hệ sinh thái ML/AI mạnh, async I/O, dễ tích hợp LLM |
| Framework API | **FastAPI** | Async, OpenAPI sẵn, validation (Pydantic), phù hợp microservice |
| Task queue | **Celery** hoặc **RQ** (Redis) | Triage chạy bất đồng bộ, không block request |
| Cache / Queue | **Redis** | Cache log/context, queue jobs, rate limit |

### 2.2 Thu thập log & dữ liệu

| Thành phần | Công nghệ | Ghi chú |
|------------|-----------|--------|
| Log aggregation | **Elasticsearch** + **Kibana** (hoặc Grafana Loki) | Đã có sẵn ở Smartpay thì tận dụng; query theo `transactionId`, `merchantId`, time range |
| Log fetch client | **elasticsearch-py** / **opensearch-py** | Nếu dùng OpenSearch tương thích ES |
| DB lưu incident history | **PostgreSQL** | Lưu incident đã xử lý để so sánh và train pattern |
| Message queue (nếu cần) | **Kafka** (consumer) | Đọc event liên quan transaction/merchant (optional) |

### 2.3 AI / LLM

| Thành phần | Công nghệ | Lý do |
|------------|-----------|--------|
| LLM chính | **OpenAI GPT-4** hoặc **Claude** | Phân tích log, so sánh pattern, gợi ý root cause & action |
| Fallback / cost | **Open-source LLM** (Llama, Mistral) qua **Ollama** hoặc **vLLM** | Giảm chi phí, chạy on-prem nếu cần |
| Embedding (tìm incident tương tự) | **sentence-transformers** hoặc **OpenAI Embeddings** | Vector search incident history |
| Vector store | **pgvector** (PostgreSQL extension) hoặc **Qdrant** | Lưu embedding, tìm incident cũ tương tự |

### 2.4 Infra & DevOps

| Thành phần | Công nghệ |
|------------|-----------|
| Container | **Docker** + **Docker Compose** (dev/staging) |
| Orchestration (production) | **Kubernetes** (nếu đã dùng) hoặc **Docker Compose** |
| Config & secrets | **Environment variables** + **.env** (dev), **Vault** hoặc K8s Secrets (prod) |
| Observability | **Prometheus** + **Grafana**; log chuẩn **structlog** / **loguru** |

---

## 3. Kiến trúc hệ thống (high-level)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Support UI /   │────▶│   Triage API     │────▶│  Log Aggregator     │
│  Slack / API    │     │   (FastAPI)      │     │  (ES/Loki)          │
└─────────────────┘     └────────┬─────────┘     └─────────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Triage Worker   │◀──── Redis (queue)
                        │  (Celery/RQ)     │
                        └────────┬─────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Incident DB     │   │  Vector Store    │   │  LLM Service     │
│  (PostgreSQL)    │   │  (pgvector)      │   │  (OpenAI/Claude) │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## 4. Các bước thực hiện (phases)

### Phase 1: Nền tảng (Foundation) — 1–2 tuần

| # | Công việc | Deliverable |
|---|-----------|-------------|
| 1.1 | Khởi tạo repo: Python, FastAPI, Docker, cấu trúc thư mục | `README`, `docker-compose.yml`, `requirements.txt` |
| 1.2 | Định nghĩa API: POST `/triage` (transactionId, orderId, merchantId, log_snippet?, error_message?) | OpenAPI spec, Pydantic models |
| 1.3 | Response schema chuẩn: issue_type, confidence, root_cause, evidence[], suggested_actions[] | Schema JSON/YAML, doc |
| 1.4 | Cấu hình Redis + Celery (hoặc RQ): job “triage” async | Worker chạy được, test enqueue job |

**Công nghệ Phase 1:** Python, FastAPI, Redis, Celery/RQ, Docker.

---

### Phase 2: Thu thập dữ liệu (Data ingestion) — 1–2 tuần

| # | Công việc | Deliverable |
|---|-----------|-------------|
| 2.1 | Client kết nối Elasticsearch/OpenSearch (hoặc Loki): query theo transactionId, merchantId, time range | Module `log_fetcher` |
| 2.2 | Mapping service → index/source (payment-service, order-service, callback-service, …) | Config (YAML/ENV) |
| 2.3 | Aggregate log từ nhiều service thành một “context” cho LLM (có giới hạn token) | Hàm `build_triage_context()` |
| 2.4 | (Optional) Kafka consumer đọc event liên quan transaction/merchant | Module optional, config |

**Công nghệ Phase 2:** elasticsearch-py, cấu hình ES/Loki, (Kafka client nếu cần).

---

### Phase 3: AI Triage core — 2–3 tuần

| # | Công việc | Deliverable |
|---|-----------|-------------|
| 3.1 | Tích hợp LLM (OpenAI/Claude): prompt nhận context (log + input), output structured (JSON/YAML) | Module `llm_triage`, prompt template |
| 3.2 | Parse và validate output LLM → đúng schema (issue_type, confidence, root_cause, evidence, suggested_actions) | Pydantic parser, retry khi parse lỗi |
| 3.3 | Thiết kế prompt: vài shot examples (Callback Failure, Payment Timeout, …), format rõ ràng | File `prompts/triage.md` hoặc trong code |
| 3.4 | Nối Phase 2 + Phase 3: worker gọi log_fetcher → build context → gọi LLM → trả kết quả | E2E flow trong worker |

**Công nghệ Phase 3:** OpenAI SDK / Anthropic SDK, Pydantic, Jinja2 hoặc f-string cho prompt.

---

### Phase 4: Incident history & similarity — 1–2 tuần

| # | Công việc | Deliverable |
|---|-----------|-------------|
| 4.1 | Schema DB: bảng incident_history (transaction_id, merchant_id, root_cause, resolution, created_at, …) | Migration PostgreSQL |
| 4.2 | Lưu mỗi lần triage (và khi support confirm) vào incident_history | API/internal call sau khi triage |
| 4.3 | Embedding root_cause + log snippet (hoặc summary); lưu vào pgvector / Qdrant | Script embedding + index |
| 4.4 | Trước khi gọi LLM: tìm top-k incident tương tự → đưa vào prompt “similar past incidents” | Module `similar_incidents`, cập nhật prompt |

**Công nghệ Phase 4:** PostgreSQL, pgvector (hoặc Qdrant), sentence-transformers hoặc OpenAI Embeddings.

---

### Phase 5: Production-ready & tích hợp — 1–2 tuần

| # | Công việc | Deliverable |
|---|-----------|-------------|
| 5.1 | Auth & rate limit cho API (API key hoặc JWT) | Middleware FastAPI |
| 5.2 | Retry, timeout, circuit breaker cho LLM và ES | Cấu hình + logging |
| 5.3 | Webhook hoặc callback URL: khi triage xong gửi kết quả (Slack, webhook custom) | Optional field trong request |
| 5.4 | Dashboard đơn giản: form nhập transactionId/merchantId, hiển thị kết quả triage (có thể dùng Streamlit hoặc React sau) | MVP UI |
| 5.5 | Document runbook: deploy, env vars, cách test với dữ liệu mẫu | `docs/RUNBOOK.md` |

**Công nghệ Phase 5:** FastAPI middleware, Slack SDK (optional), Streamlit hoặc React tùy chọn.

---

## 5. Thứ tự ưu tiên công nghệ

1. **Bắt buộc sớm:** FastAPI, Redis, Celery/RQ, LLM (OpenAI hoặc Claude), Elasticsearch client.
2. **Cần cho “so với lịch sử incident”:** PostgreSQL + pgvector (hoặc Qdrant), embedding model.
3. **Tùy hạ tầng hiện tại:** Kafka consumer chỉ thêm nếu đã dùng Kafka và cần real-time event.

---

## 6. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|--------|------------|
| LLM trả output không đúng format | Pydantic parse + retry với prompt “chỉ trả JSON”; có fallback schema |
| Log quá lớn, vượt context LLM | Giới hạn token per service, tóm tắt hoặc chỉ lấy dòng lỗi + vài dòng trước/sau |
| ES/Loki chậm hoặc down | Timeout rõ ràng, cache short TTL cho cùng transactionId, queue retry |
| Chi phí LLM cao | Dùng model nhỏ hơn cho bước “phân loại”; chỉ dùng GPT-4/Claude cho bước root cause + action |

---

## 7. Timeline gợi ý

| Phase | Thời gian | Tổng cộng |
|-------|-----------|-----------|
| Phase 1 – Foundation | 1–2 tuần | 2 tuần |
| Phase 2 – Data ingestion | 1–2 tuần | 4 tuần |
| Phase 3 – AI Triage core | 2–3 tuần | 7 tuần |
| Phase 4 – Incident history | 1–2 tuần | 9 tuần |
| Phase 5 – Production & tích hợp | 1–2 tuần | 11 tuần |

**MVP (chỉ Phase 1 + 2 + 3):** khoảng 4–7 tuần, đã có flow: nhận input → fetch log → LLM triage → trả kết quả.

---

## 8. Tài liệu tham khảo trong repo

- `docs/PLAN.md` — Kế hoạch này
- `docs/API.md` — Spec API (sẽ tạo từ OpenAPI)
- `docs/RUNBOOK.md` — Deploy & vận hành (sau Phase 5)
- `docs/PROMPTS.md` — Prompt design và vài shot examples (sau Phase 3)
