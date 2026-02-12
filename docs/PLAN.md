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

### 2.2 Thu thập log & lưu trữ (theo kiến trúc Kafka → Vector DB)

| Thành phần | Công nghệ | Ghi chú |
|------------|-----------|--------|
| Nguồn log | **Kafka** | Các service (payment, order, merchant, …) ghi log (requestId, transactionId, responseCode, data) vào Kafka |
| Log consumer | **confluent-kafka** / **aiokafka** (Python) | Một service riêng: consume → xử lý → ingest Vector DB |
| Lưu log + search | **Vector DB** (Qdrant / Weaviate / Chroma / pgvector) | Lưu log đã chuẩn hóa + embedding; BE query tại đây khi triage |
| (Tùy chọn) Incident history | **PostgreSQL** hoặc cùng Vector DB | Lưu incident đã xử lý để so sánh pattern (phase sau) |

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

**Hai thành phần chính:** (1) Log Consumer — Kafka → Vector DB; (2) Triage App — FE + BE, query Vector DB + AI. Chi tiết: [docs/ARCHITECTURE.md](ARCHITECTURE.md).

```
  payment / order / merchant ... (ghi log)
                    │
                    ▼
              ┌──────────┐      ┌─────────────────┐      ┌─────────────┐
              │  Kafka   │─────▶│ Log Consumer    │─────▶│  Vector DB  │
              │ (topics) │      │ (xử lý + ingest)│      │ (logs+vec)  │
              └──────────┘      └─────────────────┘      └──────┬──────┘
                                                                 │
  User ──▶ ┌─────────────────────────────────────────────────────┘
           │
           ▼
  ┌────────────────────────────────────────────────────────────────┐
  │  Triage App (1 service: FE + BE)                                │
  │  ┌─────────────┐    ┌─────────────────────────────────────────┐│
  │  │  Frontend   │───▶│  Backend (API) ──▶ Vector DB (search)     ││
  │  │  (input +   │    │                ──▶ LLM (triage)          ││
  │  │   kết quả)  │◀───│  response                                 ││
  │  └─────────────┘    └─────────────────────────────────────────┘│
  └────────────────────────────────────────────────────────────────┘
```

---

## 4. Các bước thực hiện (phases)

### Phase 1: Log Consumer (Kafka → Vector DB) — 1–2 tuần

| # | Công việc | Deliverable |
|---|-----------|-------------|
| 1.1 | Service consumer: subscribe Kafka topic(s) log từ payment/order/merchant | Repo hoặc module `log-consumer`, Docker |
| 1.2 | Parse message: requestId, transactionId, responseCode, service name, data; chuẩn hóa schema | Module parse + schema (Pydantic) |
| 1.3 | Chọn và kết nối Vector DB (Qdrant/Chroma/pgvector); thiết kế collection/index (metadata + vector) | Vector DB client, collection schema |
| 1.4 | Ingest: mỗi message (hoặc batch) → transform → insert Vector DB; xử lý embedding nếu dùng semantic search | Pipeline ingest chạy ổn định |

**Công nghệ Phase 1:** Python (hoặc Node), Kafka client, Vector DB (Qdrant/Chroma/Weaviate/pgvector), Docker.

---

### Phase 2: Triage App — Backend + Vector DB + AI — 1,5–2 tuần

| # | Công việc | Deliverable |
|---|-----------|-------------|
| 2.1 | Khởi tạo Triage App: FastAPI, cấu trúc FE (React/Vue hoặc đơn giản HTML) + BE | Repo/app, Docker Compose (app + Vector DB) |
| 2.2 | API: POST `/search` hoặc `/triage` — input transactionId, merchantId, (optional) log snippet, error message | OpenAPI, Pydantic request/response |
| 2.3 | Query Vector DB theo transactionId/merchantId/requestId (filter metadata); (optional) semantic search | Module `vector_search`, trả danh sách log liên quan |
| 2.4 | Gom context (log tìm được + input) → gọi LLM; parse output (issue_type, confidence, root_cause, evidence, suggested_actions) | Module `llm_triage`, prompt template |
| 2.5 | Response schema chuẩn; nối search + AI → endpoint `/triage` hoàn chỉnh | E2E: input → Vector DB → AI → response |

---

**Công nghệ Phase 2:** FastAPI, Vector DB client, OpenAI/Claude SDK, Pydantic.

---

### Phase 3: Triage App — Frontend & hoàn thiện — 1 tuần

| # | Công việc | Deliverable |
|---|-----------|-------------|
| 3.1 | UI: form nhập transactionId, merchantId, (optional) log snippet, error message | Trang input (React/Vue/HTML) |
| 3.2 | Gọi API BE (search/triage), hiển thị kết quả: log tìm được + AI (issue type, confidence, root cause, evidence, suggested actions) | Trang kết quả, có thể YAML/JSON format |
| 3.3 | (Optional) Trang “chỉ search” Vector DB không qua AI (xem raw logs) | Endpoint + UI |

**Công nghệ Phase 3:** React/Vue hoặc HTML+JS; gọi BE API.

---

### Phase 4: Production-ready (optional) — 1 tuần

| # | Công việc | Deliverable |
|---|-----------|-------------|
| 4.1 | Auth & rate limit cho API (API key hoặc JWT) | Middleware FastAPI |
| 4.2 | Retry, timeout cho LLM và Vector DB; logging chuẩn | Cấu hình + observability |
| 4.3 | Runbook: deploy Consumer + Triage App, env vars, Kafka topics, Vector DB | `docs/RUNBOOK.md` |

**Công nghệ Phase 4:** FastAPI middleware, Docker Compose / K8s.

---

## 5. Thứ tự ưu tiên công nghệ

1. **Bắt buộc:** Kafka consumer, Vector DB (Qdrant/Chroma/Weaviate/pgvector), FastAPI, LLM (OpenAI/Claude).
2. **Triage App:** Một service gồm FE + BE; BE query Vector DB + gọi AI.
3. **Không dùng:** Fetch log từ Elasticsearch/Loki — log đã được ingest từ Kafka vào Vector DB.

---

## 6. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|--------|------------|
| LLM trả output không đúng format | Pydantic parse + retry với prompt “chỉ trả JSON”; có fallback schema |
| Log quá lớn, vượt context LLM | Giới hạn số bản ghi/ token từ Vector DB; tóm tắt hoặc chỉ lấy bản ghi lỗi + metadata |
| Kafka lag / consumer chậm | Scale consumer, batch ingest; monitor offset lag |
| Vector DB chậm hoặc down | Timeout, retry; index metadata (transactionId, merchantId) để filter nhanh |
| Chi phí LLM cao | Dùng model nhỏ cho bước phân loại; GPT-4/Claude chỉ cho root cause + actions |

---

## 7. Timeline gợi ý (theo kiến trúc Kafka + Vector DB)

| Phase | Thời gian | Nội dung |
|-------|-----------|----------|
| Phase 1 – Log Consumer | 1–2 tuần | Kafka → xử lý → ingest Vector DB |
| Phase 2 – Triage BE + Vector + AI | 1,5–2 tuần | API, query Vector DB, LLM triage |
| Phase 3 – Triage FE | 1 tuần | UI input + hiển thị kết quả |
| Phase 4 – Production (optional) | 1 tuần | Auth, runbook, observability |

**MVP (Phase 1 + 2 + 3):** khoảng 3,5–5 tuần — Consumer ingest log từ Kafka vào Vector DB; user dùng UI → BE query Vector DB + AI → trả kết quả.

---

## 8. Tài liệu tham khảo trong repo

- `docs/ARCHITECTURE.md` — Kiến trúc chi tiết: Kafka → Consumer → Vector DB; Triage App (FE+BE)
- `docs/PLAN.md` — Kế hoạch này
- `docs/API.md` — Spec API (sẽ tạo từ OpenAPI)
- `docs/RUNBOOK.md` — Deploy & vận hành (sau Phase 4)
- `docs/PROMPTS.md` — Prompt design và vài shot examples (sau Phase 2)
