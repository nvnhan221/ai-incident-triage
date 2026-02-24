# Log Consumer

Consume log từ Kafka (hoặc HTTP), chuẩn hóa, ingest vào Vector DB (Qdrant).

## Setup (venv)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Cấu hình

Copy `.env.example` → `.env`, chỉnh nếu cần (QDRANT_HOST, KAFKA_*).

## Chạy

```bash
source venv/bin/activate
python main.py
```

Mặc định http://localhost:8001. API: POST /ingest, POST /ingest/batch.
