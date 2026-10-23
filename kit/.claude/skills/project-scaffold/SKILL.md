---
name: project-scaffold
description: Quy trình dựng khung dự án lần đầu từ mẫu tham chiếu (backend Hexagonal có module mẫu user, frontend Next.js, Traefik, Hurl, Playwright, script deploy). Dùng trong chế độ SCAFFOLD của /kickoff.
user-invocable: false
---

# Dựng khung dự án (chế độ SCAFFOLD)

Mẫu tham chiếu nằm ở `.claude/skills/project-scaffold/reference/`. Mẫu đã được kiểm chứng: lint, unit, integration, Hurl và Playwright đều đạt. **Chép nguyên, không tự viết lại.**

## Các bước

1. **Kiểm tra trước:**
   - Thư mục gốc chưa có `backend/` hay `frontend/`. Nếu đã có thì dừng và báo cáo, không ghi đè.
   - `docker info` chạy được. Nếu không, báo PO mở Docker Desktop.
2. **Chép mẫu** (giữ file ẩn):
   ```bash
   cp -R .claude/skills/project-scaffold/reference/. .
   ```
3. **Đặt tên dự án:** chọn `app-slug` (chữ thường, gạch ngang, ví dụ `shop-hoa`) từ tên dự án.
   - `.env.example` → `COMPOSE_PROJECT_NAME=<app-slug>`. Copy thành `.env` (không commit).
   - `frontend/src/app/layout.tsx`: tiêu đề, metadata và chữ thương hiệu ở header.
   - `backend/app/core/config.py`: `app_name`.
4. **Git:** nếu chưa có repo thì `git init -b main`. Đảm bảo `.gitignore` của mẫu đã có mặt.
5. **pm:** nếu chưa khởi tạo thì `python3 .claude/tools/pm.py init --name "<Tên dự án>"`.
6. **Tài liệu:**
   - `docs/PRD.md`: do luồng chính viết sau buổi phỏng vấn. Nếu thiếu thì tạo từ `.claude/skills/kickoff/templates/PRD.md`.
   - `docs/ARCHITECTURE.md` đã có từ mẫu. Cập nhật phần "Bối cảnh sản phẩm".
   - `pm adr "Chọn stack và kiến trúc Hexagonal" --context ... --decision ... --consequences ...`
7. **Design system:** theo skill frontend-design, lập design plan **cho sản phẩm này** (dựa vào PRD), ghi `docs/DESIGN.md`. Cập nhật token `@theme` trong `globals.css`, font trong `layout.tsx` và trang chủ cho hợp với sản phẩm. Giữ nguyên `data-testid` và cấu trúc để test mẫu vẫn chạy.
8. **Chạy thử:**
   ```bash
   make up
   pm verify --all   # timeout 600000ms
   ```
   Tất cả phải đạt. Lần đầu build image mất vài phút.
9. **Commit dựng dự án** lên `main`:
   ```bash
   git add -A && git commit -m "chore: scaffold project from techlead kit"
   ```
10. `pm link app http://localhost:8080` (đã có sẵn trong config mặc định).

## Module mẫu `user`

Mẫu có sẵn module `user` (đăng ký, xem, liệt kê). Nó là **ví dụ chuẩn** để sao chép khuôn và là dữ liệu kiểm tra cho Hurl/Playwright. **Giữ lại**, kể cả khi sản phẩm chưa cần quản lý người dùng. Khi làm tính năng thật liên quan đến người dùng (đăng nhập, phân quyền…), mở rộng module này thay vì tạo module trùng.

## Nếu một gate fail ở bước 8

Thường do môi trường: cổng 8080 bị chiếm (đổi `APP_PORT` trong `.env`), Docker thiếu RAM, mạng tải image chậm. Sửa môi trường, không sửa code mẫu. Nếu thật sự phải sửa mẫu, ghi lại chi tiết trong báo cáo.
