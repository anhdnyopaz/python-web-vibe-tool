# Kiến trúc hệ thống

## Bối cảnh sản phẩm

_(TechLead cập nhật từ docs/PRD.md: sản phẩm làm gì, cho ai, các khối chức năng chính.)_

## Sơ đồ tổng quan

```
Trình duyệt ──► Traefik (API Gateway, cổng 8080 khi dev)
                  ├── /api/*  ──► backend  (FastAPI, Python)  ──► PostgreSQL (dữ liệu)
                  │                                          └──► Redis (bộ nhớ đệm)
                  └── /*      ──► frontend (Next.js, Bun)
Production: Internet ──► Nginx Proxy Manager (HTTPS) hoặc Cloudflare Tunnel ──► Traefik ──► …
```

- **Traefik** là cổng vào duy nhất. Frontend gọi API cùng domain (`/api/...`) nên không cần CORS. Rate limit và security header nằm ở `traefik/dynamic.yml`.
- **Postgres** và **Redis** không mở cổng ra ngoài.

## Backend: Hexagonal đơn giản

```
controllers ──► usecases ──► modules (service ──► repository) ──► Postgres
     (HTTP)     (hành động       (quy tắc nghiệp vụ    (truy cập
                người dùng)       của 1 module)         dữ liệu)
```

- Mỗi tầng chỉ biết **interface** (ABC) của tầng dưới. Implementation được ghép tại một chỗ duy nhất: `backend/app/container.py`.
- Module độc lập với nhau. Khi một hành động cần nhiều module, việc phối hợp nằm ở usecase.
- Luật phụ thuộc được kiểm tra tự động bằng `lint-imports` (`backend/.importlinter`) và `tests/unit/test_architecture.py`.

## Frontend

- `src/app/` chứa các trang mỏng. `src/features/` chứa component theo tính năng. `src/services/` chứa interface API (port) và bản HTTP (adapter).
- Component chỉ dùng interface qua `useApi()`, nên unit test thay bằng bản giả được.
- Design system nằm ở `docs/DESIGN.md` và token trong `src/app/globals.css`.

## Kiểm thử

| Loại | Công cụ | Vị trí |
|---|---|---|
| Unit backend (≥80%) | pytest | `backend/tests/unit` |
| Integration | pytest + Postgres | `backend/tests/integration` |
| Unit frontend (≥70%) | bun test + Testing Library | `frontend/src/**/*.test.tsx` |
| API | Hurl | `tests/api` |
| Giao diện | Playwright | `tests/e2e/specs` |

## Module hiện có

| Module | Chức năng | API |
|---|---|---|
| user | Đăng ký, xem, liệt kê thành viên | `POST/GET /api/v1/users`, `GET /api/v1/users/{id}` |
| system | Kiểm tra tình trạng hệ thống | `GET /api/health` |
