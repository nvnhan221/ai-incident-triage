# Kiến trúc hệ thống AI Incident Triage

## 1. Nguồn dữ liệu (Log từ các service)

Các service có sẵn trong hệ thống payment:

- `payment-service`
- `order-service`
- `merchant-service`
- (các service khác: reconciliation, callback, POS, …)

Khi thực hiện giao dịch, mỗi service ghi log với các trường:

- **requestId**
- **transactionId**
- **responseCode**
- **data** (payload tương ứng)

Các log này được **ghi nhận vào Kafka** (topic log hoặc per-service topics).

---

## 2. Hai thành phần chính

Hệ thống gồm **2 phần**:

### 2.1 Log Consumer Service (Ingest pipeline)

**Vai trò:** Consume log messages từ Kafka → xử lý → ingest vào Vector DB.

```
Kafka (log topics)  ──▶  Consumer Service  ──▶  Vector DB
```

- **Input:** Messages từ Kafka (log từ payment-service, order-service, merchant-service, …).
- **Xử lý:** Parse log, chuẩn hóa (requestId, transactionId, responseCode, service name, data), tạo embedding nếu cần.
- **Output:** Ghi vào Vector DB (document + vector để search sau).

### 2.2 Triage App (FE + BE) — Một service duy nhất

**Vai trò:** Public UI cho người dùng + Backend (API, AI, truy vấn Vector DB).

```
User  ──▶  UI (FE)  ──▶  Backend (BE)  ──┬──▶  Vector DB (tìm log/context)
                                         └──▶  AI/LLM (triage, gợi ý)
```

- **FE:** Form nhập (transactionId, orderId, merchantId, log snippet, error message…) + hiển thị kết quả tìm kiếm và kết quả AI triage.
- **BE:**
  - Nhận input từ user.
  - **Lấy thông tin từ Vector DB:** search theo transactionId, merchantId, requestId hoặc semantic search.
  - **Apply AI:** đưa context (log tìm được + input) vào LLM → root cause, evidence, suggested actions.
  - Trả kết quả về cho UI.

---

## 3. Sơ đồ tổng thể

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Các service hiện có (ghi log vào Kafka)                                  │
│  payment-service │ order-service │ merchant-service │ ...                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ logs (requestId, transactionId, responseCode, data)
                                ▼
                        ┌───────────────┐
                        │    Kafka      │
                        │  (log topics) │
                        └───────┬───────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  Service 1: Log Consumer                                                   │
│  - Consume messages từ Kafka                                              │
│  - Xử lý / chuẩn hóa log                                                  │
│  - Ingest vào Vector DB                                                   │
└───────────────────────────────┬───────────────────────────────────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │  Vector DB    │
                        │ (logs + vec)  │
                        └───────┬───────┘
                                │
                                │ search (transactionId, merchantId, semantic)
                                ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  Service 2: Triage App (FE + BE trong 1 service)                          │
│  ┌─────────────────┐    ┌─────────────────────────────────────────────┐ │
│  │  Frontend (UI)  │───▶│  Backend (API)                                │ │
│  │  - Input form   │    │  - Nhận input                                 │ │
│  │  - Kết quả      │    │  - Query Vector DB → lấy log/context         │ │
│  └─────────────────┘    │  - Gọi AI/LLM → triage, root cause, actions  │ │
│                         │  - Trả kết quả                                │ │
│                         └─────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Luồng dữ liệu chi tiết

### 4.1 Luồng Ingest (Kafka → Vector DB)

1. Các service ghi log (requestId, transactionId, responseCode, data) → produce vào Kafka.
2. **Log Consumer** subscribe topic(s), consume message.
3. Parse message (JSON), chuẩn hóa schema (service name, timestamp, transactionId, …).
4. (Tùy chọn) Tạo embedding cho nội dung log (để semantic search).
5. Insert/upsert vào Vector DB (metadata + vector).

### 4.2 Luồng Triage (User → UI → BE → Vector DB + AI)

1. User mở UI, nhập ví dụ: `transactionId`, `merchantId`, (optional) log snippet / error message.
2. FE gửi request sang BE (ví dụ POST `/search` hoặc POST `/triage`).
3. BE:
   - Query **Vector DB** theo transactionId/merchantId/requestId (hoặc semantic) → lấy tập log liên quan.
   - Gom context (log + input user) → gọi **AI/LLM**.
   - LLM trả: issue type, confidence, root cause, evidence, suggested actions.
4. BE trả kết quả về FE → UI hiển thị.

---

## 5. Công nghệ gợi ý (theo kiến trúc này)

| Thành phần | Công nghệ |
|------------|-----------|
| **Log Consumer** | Python/Node; Kafka client (confluent-kafka / kafka-python); Vector DB client (Qdrant, Weaviate, pgvector, …) |
| **Vector DB** | Qdrant / Weaviate / Chroma / pgvector (chọn 1) |
| **Triage Backend** | Python + FastAPI (hoặc Node + Express); SDK Vector DB; OpenAI/Claude SDK |
| **Triage Frontend** | React / Next.js / Vue (hoặc đơn giản: HTML + JS, hoặc Streamlit nếu chỉ cần nội bộ) |

---

## 6. Tóm tắt

- **Một consumer:** Kafka → xử lý log → ingest Vector DB.
- **Một app (FE + BE):** UI input → BE query Vector DB + gọi AI → trả kết quả cho user.
- **Không cần** fetch log từ Elasticsearch/Loki trong bước triage — dữ liệu đã nằm trong Vector DB do consumer ingest từ Kafka.
