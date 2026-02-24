# AI Incident Triage

Hệ thống gồm 2 phần:

1. **Log Consumer** — Nhận log (Kafka hoặc HTTP), chuẩn hóa, ingest vào Vector DB (Qdrant).
2. **Triage App** — FE + BE: form nhập mã đơn/merchant → query Vector DB + gọi AI → hiển thị kết quả.

## Cấu hình (.env)

Cả hai service đọc cấu hình từ file **.env** trong thư mục tương ứng (không dùng biến môi trường tay). Copy từ `.env.example` rồi chỉnh nếu cần:

```bash
cp triage_app/backend/.env.example triage_app/backend/.env
cp log_consumer/.env.example log_consumer/.env
```

Trong `.env` của Triage Backend có thể thêm `OPENAI_API_KEY=sk-...` để bật AI triage. File `.env` không commit lên git.

## Yêu cầu

- Python 3.11+
- Docker & Docker Compose (nếu chạy bằng Docker)
- (Tùy chọn) OpenAI API key cho tính năng AI triage

## Setup Python (venv) — cho 2 project backend

Áp dụng cho **log_consumer** và **triage_app/backend**. Trong từng thư mục project, chạy:

```bash
# Tạo virtual environment
python3 -m venv venv

# Kích hoạt (macOS/Linux)
source venv/bin/activate
# Windows: venv\Scripts\activate

# Cài dependency
pip install --upgrade pip
pip install -r requirements.txt
```

Ví dụ:

```bash
# Log Consumer
cd log_consumer
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Triage Backend (terminal khác hoặc sau khi deactivate)
cd triage_app/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

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
2. Log Consumer (sau khi [setup venv](#setup-python-venv--cho-2-project-backend) trong `log_consumer/`):
   ```bash
   cd log_consumer
   source venv/bin/activate
   python main.py
   ```
   Mặc định http://localhost:8001. Ingest log qua POST http://localhost:8001/ingest hoặc /ingest/batch.
3. Triage App (Backend + Frontend):
   - Backend (sau khi setup venv trong `triage_app/backend/`):
     ```bash
     cd triage_app/backend
     source venv/bin/activate
     python main.py
     ```
     Mặc định http://localhost:8000.
   - Frontend (Next.js) — chọn một trong hai:
     - **Cách A — Build tĩnh, serve từ Backend:**  
       `cd triage_app/frontend && npm install && npm run build`  
       Sau đó chạy backend như trên; mở http://localhost:8000/app/ (Backend serve thư mục `frontend/out/`).
     - **Cách B — Chạy dev riêng:**  
       `cd triage_app/frontend && npm install && cp .env.local.example .env.local && npm run dev`  
       Mở http://localhost:3000. Trong `.env.local` đặt `NEXT_PUBLIC_API_URL=http://localhost:8000` để gọi API.
4. Cấu hình: copy `.env.example` thành `.env` trong từng service và chỉnh nếu cần. Thêm `OPENAI_API_KEY` vào `.env` của Backend để bật AI triage.

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
│   └── frontend/        # Next.js (App Router + Tailwind)
│       ├── app/         # layout, page
│       ├── lib/        # api client
│       ├── package.json
│       └── out/        # (sau npm run build) — Backend serve /app từ đây
├── scripts/
│   ├── ingest_sample_logs.py
│   └── sample_logs_y20ki9r6.json
├── docker-compose.yml
└── README.md
```

## API Triage App

- **POST /search** — Body: `{ "order_no": "Y20KI9R6", "merchant_id": "...", "request_id": "..." }` → Trả danh sách logs từ Vector DB.
- **POST /triage** — Cùng body + optional `log_snippet`, `error_message` → Trả logs + kết quả AI (issue_type, confidence, root_cause, evidence, suggested_actions).
