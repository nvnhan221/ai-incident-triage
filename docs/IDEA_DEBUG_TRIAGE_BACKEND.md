# Hướng dẫn cấu hình + Debug Triage Backend với IntelliJ IDEA

## 1. Yêu cầu

- **IntelliJ IDEA** (bản có hỗ trợ Python, hoặc **PyCharm**).
- **Python 3.11+** đã cài trên máy.
- **Qdrant** đang chạy (Docker: `docker run -p 6333:6333 qdrant/qdrant` hoặc `docker compose up -d` cho qdrant).

---

## 2. Cấu hình Python interpreter

1. **File → Project Structure** (Ctrl+Alt+S) → **Project** → **Project SDK**: chọn **Python 3.11** (hoặc Add SDK → chọn đường dẫn python).
2. **File → Settings → Project: ai-incident-triage → Python Interpreter**: chọn cùng interpreter.
3. (Khuyến nghị) Tạo **Virtualenv** cho project:
   - Trong **Python Interpreter** → bấm bánh răng → **Add** → **Virtualenv Environment** → **New** → chọn base interpreter Python 3.11 → **OK**.
   - Cài dependency: mở terminal trong IDE, chạy:
     ```bash
     cd triage_app/backend && pip install -r requirements.txt
     ```

---

## 3. Tạo Run/Debug Configuration

### Cách A: Dùng cấu hình có sẵn trong repo

Repo đã có sẵn 2 run configuration trong **.idea/runConfigurations/**:

| Config | Mô tả |
|--------|--------|
| **Triage Backend** | Chạy `triage_app/backend/main.py`; đọc cấu hình từ **triage_app/backend/.env**. |
| **Triage Backend (reload)** | Chạy `uvicorn app.main:app --reload`; cùng file .env. |

1. Trên thanh toolbar, mở dropdown **Run/Debug Configurations**.
2. Chọn **"Triage Backend"** hoặc **"Triage Backend (reload)"**.
3. Bấm **Debug** (🐛) để chạy ở chế độ debug, hoặc **Run** (▶) để chạy bình thường.

### Cách B: Tạo mới thủ công

1. **Run → Edit Configurations...** (hoặc bấm dropdown cạnh nút Run → **Edit Configurations**).
2. Bấm **+** → chọn **Python**.
3. Điền:
   - **Name:** `Triage Backend`
   - **Script path** hoặc **Module name** (chọn một trong hai):

     **Option 1 — Chạy file `main.py`:**
   - **Script path:** `$PROJECT_DIR$/triage_app/backend/main.py`
   - **Working directory:** `$PROJECT_DIR$/triage_app/backend`

     **Option 2 — Chạy bằng module uvicorn (có --reload):**
   - **Module name:** `uvicorn`
   - **Parameters:** `app.main:app --reload --host 0.0.0.0 --port 8000`
   - **Working directory:** `$PROJECT_DIR$/triage_app/backend`

4. **Env file:** mục **Environment file** trỏ tới `triage_app/backend/.env`. Tạo file `.env` từ bản mẫu:
   ```bash
   cp triage_app/backend/.env.example triage_app/backend/.env
   ```
   Chỉnh `.env` nếu cần (QDRANT_HOST, QDRANT_PORT, TRIAGE_PORT, OPENAI_API_KEY cho AI triage).

5. **Python interpreter:** chọn interpreter đã cấu hình (vd: Python 3.11 hoặc virtualenv).

6. **OK** → **Apply**.

---

## 4. Chạy và Debug

- **Run:** chọn config **Triage Backend** → bấm **Run** (▶).
- **Debug:** chọn **Triage Backend** → bấm **Debug** (🐛).

Sau khi start:

- API: **http://localhost:8000**
- Docs: **http://localhost:8000/docs**
- Health: **http://localhost:8000/health**
- UI: **http://localhost:8000/app/** (cần có thư mục `triage_app/frontend` với `index.html`).

### Đặt breakpoint

1. Mở file trong `triage_app/backend/app/` (vd: `main.py`, `vector_client.py`, `llm.py`).
2. Bấm vào lề trái số dòng (hoặc Ctrl+F8) để đặt **breakpoint**.
3. Chạy **Debug** → gửi request (vd: POST http://localhost:8000/search với body `{"order_no":"Y20KI9R6"}`) → execution sẽ dừng tại breakpoint.

---

## 5. Troubleshooting

| Vấn đề | Cách xử lý |
|--------|------------|
| **ModuleNotFoundError: No module named 'app'** | Đảm bảo **Working directory** = `triage_app/backend`. |
| **ModuleRootManager.getInstance … must not be null** | Run config cần gắn **đúng Python module**. Vào **Edit Configurations** → chọn **Triage Backend** → mục **Module** chọn **backend** (module Python của `triage_app/backend`, tên từ file `backend.iml`). **Không** để trống hoặc "No module" — IntelliJ sẽ truyền null và báo lỗi. |
| **Connection refused Qdrant** | Chạy Qdrant: `docker run -p 6333:6333 qdrant/qdrant` hoặc `docker compose up -d`. |
| **Frontend không load (/app/)** | Đảm bảo có thư mục `triage_app/frontend/index.html` (cùng repo). |
| **Breakpoint không dừng** | Chạy bằng **Debug** (🐛), không phải Run. |
| **Port 8000 đã dùng** | Đổi env `TRIAGE_PORT=8001` (hoặc port khác). |

---

## 6. File cấu hình có sẵn

- **`.idea/runConfigurations/Triage_Backend.run.xml`** — chạy `main.py`, working dir = `triage_app/backend`, env: `QDRANT_HOST`, `QDRANT_PORT`, `TRIAGE_PORT`.
- **`.idea/runConfigurations/Triage_Backend__reload_.run.xml`** — chạy module `uvicorn` với `--reload`.

**Lưu ý:** Nếu project chưa được nhận dạng là Python (module type trong .iml là Java), cần cài **Plugin Python** (Settings → Plugins → Python) và/hoặc **Add Python SDK** (Project Structure → Project SDK). Sau đó có thể cần tạo lại run config theo **Cách B** (chọn đúng Python interpreter). Nếu đã thấy config **Triage Backend** trong dropdown nhưng chạy báo lỗi interpreter, vào **Edit Configurations** → chọn config → **Python interpreter** → chọn SDK Python 3.11+.
