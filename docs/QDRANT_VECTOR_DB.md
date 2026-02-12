# Vector DB Qdrant — Chi tiết và lý do sử dụng

## 1. Qdrant là gì?

**Qdrant** là **vector database** (cơ sở dữ liệu vector) mã nguồn mở, viết bằng **Rust**, thiết kế cho ứng dụng AI và tìm kiếm ngữ nghĩa (semantic search).

- **Vector:** mỗi bản ghi được biểu diễn bằng một mảng số (embedding) do model AI sinh ra. Các bản ghi “giống nhau” về nghĩa sẽ có vector gần nhau trong không gian.
- **Vector DB:** lưu trữ vector và cho phép tìm nhanh “điểm gần nhất” (nearest neighbour) theo độ tương tự (cosine, dot product, euclidean…).

Trong dự án AI Incident Triage, mỗi **log** sau khi chuẩn hóa được lưu vào Qdrant kèm **payload** (metadata: `order_no`, `merchant_id`, `module`, `operation`, …) và có thể kèm **vector** (embedding của nội dung log) để vừa **filter chính xác** theo mã đơn/merchant, vừa **tìm kiếm theo nghĩa** nếu cần.

---

## 2. Tính năng chính của Qdrant

### 2.1 Tìm kiếm vector (Vector search)

- Dùng thuật toán **HNSW** (Hierarchical Navigable Small World) — tối ưu cho approximate nearest neighbour (ANN), cân bằng giữa tốc độ và độ chính xác.
- Hỗ trợ nhiều **metric**:
  - **Cosine** — phổ biến cho embedding văn bản.
  - **Dot product** — phù hợp khi vector đã chuẩn hóa.
  - **Euclidean**, **Manhattan** — khoảng cách hình học.

### 2.2 Payload (metadata) mạnh

- Mỗi điểm (point) = **vector + payload** (JSON).
- Payload dùng để:
  - **Lọc (filter)** trước khi search: ví dụ chỉ tìm log có `order_no = "Y20KI9R6"` hoặc `merchant_id = "9800000367"`.
  - Lưu thông tin hiển thị: `module`, `operation`, `text`, `payload` (log gốc)…
- Kiểu dữ liệu payload: keyword (string), integer, float, boolean, datetime, geo. Có thể đánh index payload để filter nhanh.

Trong project này, ta đang dùng **filter theo payload** (order_no, merchant_id, request_id) là chính; vector có thể dùng sau khi bật embedding cho semantic search.

### 2.3 Filter kết hợp với vector search

- **Hybrid:** vừa filter theo điều kiện (order_no, merchant_id, thời gian…), vừa sort theo điểm tương tự vector.
- Hỗ trợ điều kiện phức tạp: match, range, must/should, geo…

### 2.4 Hiệu năng

- Viết bằng Rust → tốc độ và an toàn bộ nhớ.
- Benchmark thường cho thấy Qdrant có **throughput (RPS)** cao và **latency** thấp so với nhiều vector DB khác.
- Tùy chọn **quantization** (nén vector), **on_disk** (vector lưu trên đĩa) để scale dữ liệu lớn mà vẫn kiểm soát RAM.

### 2.5 Triển khai linh hoạt

- **Self-hosted:** chạy bằng Docker, binary; có Python client chính thức (`qdrant-client`).
- **Qdrant Cloud:** managed, có free tier.
- **Distributed:** sharding, replication cho production.

---

## 3. Tại sao nên dùng Qdrant trong dự án AI Incident Triage?

### 3.1 Phù hợp với luồng dữ liệu

- **Consumer** ingest log → chuẩn hóa → cần lưu **metadata** (order_no, merchant_id, request_id, module, operation, …) và có thể thêm **vector** (embedding) sau.
- **Triage BE** cần:
  - **Tìm theo mã:** filter chính xác theo `order_no`, `merchant_id`, `request_id` → Qdrant filter payload làm rất tốt.
  - (Tương lai) **Tìm theo nghĩa:** “log lỗi callback timeout” → cần vector + semantic search → Qdrant hỗ trợ sẵn.

Một DB vừa filter mạnh vừa vector search giúp không phải kết hợp nhiều hệ thống (VD: PostgreSQL + Elasticsearch + vector service).

### 3.2 Payload = metadata log

- Log sau chuẩn hóa có nhiều trường: order_no, order_id, trace_id, merchant_id, amount, channel, module, operation, resp_code, status, text, payload (raw).
- Qdrant lưu tất cả dưới dạng **payload**; filter và trả về đúng những gì API cần → đơn giản, ít layer.

### 3.3 Một collection, nhiều cách truy vấn

- Có thể dùng **một collection** (vd: `payment_logs`) cho mọi log; phân tách theo tenant/merchant bằng **filter payload** (multitenancy) thay vì tạo nhiều collection → dễ vận hành, tận dụng index chung.

### 3.4 Mã nguồn mở và Python

- Open source → không phụ thuộc vendor, có thể self-host.
- Client Python chính thức ổn định, API rõ ràng (upsert, scroll, search với filter) → dễ tích hợp với FastAPI (Log Consumer và Triage BE).

### 3.5 Có thể chỉ dùng filter (không bắt buộc embedding ngay)

- Hiện tại có thể dùng **vector size = 1** (dummy) và chỉ **scroll + filter** theo payload để lấy log theo order_no/merchant_id → vẫn hoạt động tốt.
- Sau này bật embedding và semantic search thì không cần đổi DB, chỉ cần thêm vector thật và đổi query.

### 3.6 Phù hợp RAG / AI pipeline

- Qdrant thường dùng trong RAG (retrieval for LLM). Ở đây bước “retrieve” = lấy log liên quan từ Vector DB, rồi đưa context cho LLM triage → cùng mô hình, Qdrant phù hợp.

---

## 4. So sánh nhanh với một số lựa chọn khác

| Tiêu chí           | Qdrant      | Chroma       | Pinecone      | pgvector (PostgreSQL) |
|--------------------|------------|--------------|---------------|------------------------|
| Open source        | Có         | Có           | Không (SaaS)  | Có (extension)        |
| Filter metadata    | Rất mạnh   | Có           | Có            | Có (SQL)               |
| Hiệu năng ANN      | Cao (Rust) | Ổn           | Cao (managed) | Phụ thuộc scale        |
| Self-host đơn giản | Docker 1 container | Dễ | Không         | Cần PostgreSQL         |
| Python client      | Chính thức | Chính thức   | Chính thức    | psycopg2 + pgvector    |
| Phù hợp log + filter + (sau) vector | Tốt | Tốt cho prototype | Tốt nếu dùng cloud | Tốt nếu đã có Postgres |

**Kết luận:** Qdrant cân bằng giữa self-host, hiệu năng, filter mạnh và vector search, phù hợp kiến trúc “Kafka → Consumer → Vector DB” và “Triage BE query theo order_no/merchant_id + (sau) semantic”.

---

## 5. Cách dự án đang dùng Qdrant

- **Collection:** `payment_logs` (tên có thể đổi qua env `QDRANT_COLLECTION`).
- **Point:** mỗi log chuẩn hóa = 1 point:
  - **id:** duy nhất (vd: `requestId_startTime`).
  - **vector:** hiện tại dummy size 1 (để đủ schema); sau có thể đổi sang vector embedding thật.
  - **payload:** toàn bộ trường của `NormalizedLog` (request_id, order_no, merchant_id, module, operation, resp_code, status, text, payload raw…).
- **Query:**
  - **Search/Triage:** scroll (hoặc search) với **filter** theo `order_no`, `merchant_id`, `request_id` → lấy danh sách log → đưa cho LLM.

Chi tiết schema log và payload: xem `docs/LOG_SCHEMA.md`. Code tích hợp: `log_consumer/app/vector_store.py`, `triage_app/backend/app/vector_client.py`.

---

## 6. Tài liệu tham khảo

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Payload & Filtering](https://qdrant.tech/documentation/concepts/payload/)
- [Collections](https://qdrant.tech/documentation/concepts/collections/)
- [Qdrant Cloud](https://qdrant.tech/documentation/cloud-intro/) (nếu dùng managed)
