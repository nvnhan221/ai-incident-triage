# Triage Frontend (Next.js)

- **Next.js 14** (App Router) + **Tailwind CSS** + **TypeScript**
- Form nhập mã đơn / merchant / request → Tìm logs hoặc Triage (AI) → hiển thị kết quả

## Chạy dev

```bash
npm install
cp .env.local.example .env.local
# Chỉnh .env.local: NEXT_PUBLIC_API_URL=http://localhost:8000 (nếu backend chạy port 8000)
npm run dev
```

Mở http://localhost:3000. Backend cần chạy tại `NEXT_PUBLIC_API_URL`.

## Build và serve từ Backend

```bash
npm install
npm run build
```

Thư mục `out/` sẽ được tạo. Chạy Triage Backend (FastAPI); Backend sẽ serve `/app` từ `frontend/out/`. Mở http://localhost:8000/app/ (không cần set `NEXT_PUBLIC_API_URL` — gọi API cùng origin).

## Cấu trúc

- `app/layout.tsx`, `app/page.tsx` — layout và trang chính
- `app/globals.css` — Tailwind + biến CSS
- `lib/api.ts` — client gọi POST /search, POST /triage
