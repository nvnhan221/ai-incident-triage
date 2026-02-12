# AI Incident Triage

Hệ thống gồm 2 phần:

1. **Log Consumer** — Nhận log (Kafka hoặc HTTP), chuẩn hóa, ingest vào Vector DB (Qdrant).
2. **Triage App** — FE + BE: form nhập mã đơn/merchant → query Vector DB + gọi AI → hiển thị kết quả.

## Yêu cầu

- Python 3.11+
- Docker & Docker Compose (nếu chạy bằng Docker)
- (Tùy chọn) OpenAI API key cho tính năng AI triage

## Chạy bằng Docker Compose

```bash
docker compose up -d
```

- **Qdrant:** http://localhost:6333
- **Log Consumer:** http://localhost:8001 (POST /ingest hoặc /ingest/batch để đẩy log)
- **Triage App:** http://localhost:8000 (API + FE tại /app/)

### Ingest log mẫu (mã đơn Y20KI9R6)

Sau khi `docker compose up`, gọi ingest batch với file log mẫu:

```bash
curl -X POST http://localhost:8001/ingest/batch \
  -H "Content-Type: application/json" \
  -d @scripts/sample_logs_y20ki9r6.json
```

Hoặc dùng script Python:

```bash
pip install httpx
python scripts/ingest_sample_logs.py
```

Sau đó mở http://localhost:8000/app/ (hoặc http://localhost:8000/app/index.html), nhập mã đơn **Y20KI9R6** → bấm **Tìm logs** hoặc **Triage (AI)**.

## Chạy local (không Docker)

1. Chạy Qdrant (Docker): `docker run -p 6333:6333 qdrant/qdrant`
2. Log Consumer:
   ```bash
   cd log_consumer && pip install -r requirements.txt && python main.py
   ```
   Mặc định chạy tại http://localhost:8001. Ingest log qua POST http://localhost:8001/ingest hoặc /ingest/batch.
3. Triage App:
   ```bash
   cd triage_app/backend && pip install -r requirements.txt && python main.py
   ```
   Mặc định http://localhost:8000. Mở http://localhost:8000/app/ để dùng form (cần copy thư mục `frontend` vào `triage_app/backend/../frontend`).
4. Cấu hình AI: đặt biến môi trường `OPENAI_API_KEY` (và tùy chọn `OPENAI_MODEL`) để dùng Triage (AI). Nếu không có, API vẫn trả về danh sách log và tóm tắt đơn giản.

## Cấu trúc repo

```
├── docs/
│   ├── ARCHITECTURE.md   # Kiến trúc Kafka → Consumer → Vector DB; Triage FE+BE
│   ├── LOG_SCHEMA.md    # Schema log và chuẩn hóa
│   └── PLAN.md
├── log_consumer/        # Service 1: consume log → Vector DB
│   ├── app/
│   │   ├── main.py      # FastAPI: /ingest, /ingest/batch; optional Kafka task
│   │   ├── normalizer.py
│   │   ├── schemas.py
│   │   ├── vector_store.py
│   │   └── kafka_consumer.py
│   ├── requirements.txt
│   └── Dockerfile
├── triage_app/
│   ├── backend/         # Service 2 BE: /search, /triage
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── schemas.py
│   │   │   ├── vector_client.py
│   │   │   └── llm.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/        # Form + gọi BE, hiển thị kết quả
│       └── index.html
├── scripts/
│   ├── ingest_sample_logs.py
│   └── sample_logs_y20ki9r6.json
├── docker-compose.yml
└── README.md
```

## API Triage App

- **POST /search** — Body: `{ "order_no": "Y20KI9R6", "merchant_id": "...", "request_id": "..." }` → Trả danh sách logs từ Vector DB.
- **POST /triage** — Cùng body + optional `log_snippet`, `error_message` → Trả logs + kết quả AI (issue_type, confidence, root_cause, evidence, suggested_actions).
