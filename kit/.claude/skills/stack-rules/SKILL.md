---
name: stack-rules
description: Stack công nghệ cố định, cấu trúc thư mục, lệnh Makefile và quy ước chung của dự án (Docker, FastAPI, Postgres, Redis, Next.js + Tailwind + TypeScript + Bun, Traefik, Hurl, Playwright). Dùng khi viết code, thêm thư viện, chạy lệnh hoặc dựng dự án.
user-invocable: false
---

# Stack cố định (không đổi nếu không có ADR được PO đồng ý)

| Phần | Công nghệ | Ghi chú |
|---|---|---|
| Đóng gói | Docker + Docker Compose | Máy người dùng chỉ cần Docker Desktop. MỌI lệnh chạy qua `make` hoặc `docker compose`. |
| API Gateway | Traefik v3 | Cổng duy nhất. `/api/*` → backend, còn lại → frontend. Cấu hình ở `traefik/dynamic.yml`. |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic | Kiến trúc Hexagonal, xem skill `hexagonal-backend`. |
| Database | PostgreSQL 17 | Chỉ truy cập qua repository. Đổi schema phải có migration. |
| Cache/queue | Redis 8 | Truy cập qua interface `ICache` (thêm interface mới nếu cần queue hoặc lock). |
| Frontend | Next.js 16 (App Router), TypeScript strict, Tailwind CSS 4, Bun | Xem skill `frontend-rules`. Bắt buộc dùng skill frontend-design. |
| Unit test | pytest + pytest-cov (≥ 80%), bun test + Testing Library + happy-dom (≥ 70%) | BẮT BUỘC. |
| API test | Hurl (`tests/api/*.hurl`) | Chạy qua Traefik trong Docker. |
| UI test | Playwright (`tests/e2e/specs/*.spec.ts`) | Desktop Chrome + mobile Pixel 7. |
| Lint | ruff, import-linter (luật kiến trúc), tsc | `make lint`. |

# Cấu trúc dự án

```
.
├── CLAUDE.md, Makefile, docker-compose.yml, docker-compose.prod.yml, .env.example
├── traefik/dynamic.yml          # định tuyến + middleware (rate limit, security headers)
├── backend/                     # FastAPI — xem hexagonal-backend
├── frontend/                    # Next.js — xem frontend-rules
├── tests/api/                   # Hurl
├── tests/e2e/                   # Playwright (image riêng có sẵn browser + bun)
├── db/init/                     # SQL chạy lần đầu (tạo DB app_test cho integration test)
├── deploy/                      # script deploy VPS / backup / restore — xem deploy-playbook
├── docs/PRD.md, ARCHITECTURE.md, DESIGN.md, BOARD.md (tự sinh), decisions/ (ADR)
├── .pm/                         # dữ liệu quản lý dự án (commit vào git, trừ .pm/logs)
└── .claude/                     # agent, skill, hook, tools/pm.py — KHÔNG sửa trừ khi PO yêu cầu
```

# Lệnh

| Việc | Lệnh |
|---|---|
| Bật app (http://localhost:8080, API docs `/api/docs`, Traefik `:8090`) | `make up` |
| Tắt (giữ dữ liệu) / xem log / trạng thái | `make down` / `make logs` / `make ps` |
| Lint + kiến trúc | `make lint` |
| Unit test | `make test-unit` (hoặc `test-unit-be`, `test-unit-fe`) |
| Integration + Hurl | `make test-api` |
| Playwright | `make test-e2e` |
| Toàn bộ | `make test` (hoặc `pm verify --all`) |
| Migration | `make migration name=add_orders`, rồi `make migrate` |
| Link chia sẻ bản dev | `make share` / `make share-stop` |
| Lệnh Python tuỳ ý | `docker compose run --rm backend <lệnh>` |
| Lệnh Bun tuỳ ý | `docker compose run --rm --no-deps frontend bun <lệnh>` |

# Thêm thư viện

- **Python:** thêm vào `backend/requirements.txt` (chạy production) hoặc `requirements-dev.txt` (test/lint), **ghim phiên bản chính xác** (`==`), rồi `docker compose build backend`.
- **Frontend:** `docker compose run --rm --no-deps frontend bun add <pkg>@<version>` (thêm `-d` nếu là dev). Lệnh này tự cập nhật `package.json` và `bun.lock`. Không sửa tay `bun.lock`.
- Thư viện đáng kể (ORM khác, UI kit, auth, thanh toán…) cần **ADR** (`pm adr`) và phải đúng tinh thần stack.

# Quy ước chung

- Tên hàm, biến, class, file, bảng, cột, endpoint: **tiếng Anh**. Python dùng `snake_case`; TS biến/hàm dùng `camelCase`, component/class dùng `PascalCase`; bảng DB dạng số nhiều `snake_case`.
- Thông báo cho người dùng cuối (lỗi API, chữ trên UI): **tiếng Việt**, rõ ràng, chỉ cách khắc phục.
- REST API: `/api/v1/<resources>`. Lỗi luôn có dạng `{"error": {"code": "...", "message": "..."}}` (đã có sẵn trong `error_handlers.py`). Phân trang bằng `limit`/`offset`, trả về `{"items": [...]}`.
- Thời gian lưu UTC (`DateTime(timezone=True)`). Định dạng hiển thị đặt ở frontend.
- Cấu hình qua biến môi trường (`app/core/config.py`). Không hard-code URL, mật khẩu.
- Secret: `.env` (dev, không commit), `.deploy/.env.prod` (prod, không commit). Không in secret ra log hay báo cáo.
- Tên `data-testid` dạng `kebab-case` mô tả vai trò: `register-submit`, `order-list`.
