# Triage Backend

API /search, /triage — query Vector DB + LLM. Frontend Next.js có thể chạy riêng hoặc build ra `../frontend/out/` để Backend serve tại /app.

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

Copy `.env.example` → `.env`. Thêm `OPENAI_API_KEY` để bật AI triage.

## Chạy

```bash
source venv/bin/activate
python main.py
```

Mặc định http://localhost:8000. API: POST /search, POST /triage. UI: http://localhost:8000/app/ (nếu đã build frontend vào `../frontend/out/`).
