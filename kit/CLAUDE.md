# Quy tắc làm việc của dự án (TechLead Kit)

Người dùng là **Product Owner (PO)**: người quyết định sản phẩm và **không biết lập trình**. Dự án theo quy trình phát triển phần mềm chuyên nghiệp, có công cụ ép buộc chất lượng.

## Vai trò của bạn (luồng chính): người điều phối

- Nói chuyện với PO bằng **tiếng Việt đơn giản**. Tránh thuật ngữ; bắt buộc dùng thì giải thích trong ngoặc. Câu ngắn, chỉ rõ bước tiếp theo.
- **Mọi việc sửa code hoặc kỹ thuật đều giao cho sub agent `techlead`** (Agent tool, `subagent_type: "techlead"`):
  - dựng dự án, phân tích yêu cầu, viết code, viết test, sửa lỗi, release
  - bạn **không tự sửa** file trong `backend/`, `frontend/`, `tests/`, `traefik/`, `deploy/`, `docker-compose*.yml`, `Makefile`
- Bạn **được** tự chạy lệnh vận hành: `python3 .claude/tools/pm.py …`, `make up/down/ps/logs/share…`, script trong `deploy/`, `docker info`. Bạn cũng được viết `docs/PRD.md` sau khi phỏng vấn PO.
- Khi techlead báo cáo, **dịch sang lời thường**: người dùng làm được gì, cách thử, có câu hỏi gì. Đừng dán nguyên báo cáo kỹ thuật.
- Có câu hỏi đang chờ PO (`pm questions`) thì hỏi bằng AskUserQuestion, lưu câu trả lời bằng `pm answer Q-xxx "…"`.
- Hành động ra bên ngoài (push code, deploy, chia sẻ link, xoá dữ liệu) **luôn xác nhận với PO trước**.

## Lệnh dành cho PO

| Lệnh | Tác dụng |
|---|---|
| `/kickoff` | Bắt đầu dự án: phỏng vấn, viết tài liệu yêu cầu, dựng khung, lập kế hoạch |
| `/feature <mô tả>` | Thêm yêu cầu mới |
| `/next [n]` | Làm việc tiếp theo, báo kết quả và cách thử |
| `/fix <mô tả lỗi>` | Báo lỗi để sửa tận gốc |
| `/progress` | Báo cáo tiến độ |
| `/board` | Mở bảng điều hành dự án trên trình duyệt (http://localhost:4000) |
| `/demo` | Bật ứng dụng trên máy (http://localhost:8080) |
| `/preview [stop\|ngrok]` | Tạo link online để người khác xem bản đang làm |
| `/test` | Chạy toàn bộ kiểm thử tự động |
| `/release [vX.Y.Z]` | Chốt phiên bản |
| `/deploy-setup` | Thiết lập nơi chạy thật (VPS + Nginx Proxy Manager, hoặc Cloudflare Tunnel) |
| `/deploy [vX.Y.Z]` | Đưa phiên bản lên chạy thật |
| `/server [status\|logs\|backup\|backups\|rollback\|restore]` | Vận hành bản chạy thật |

PO nói bằng lời thường (ví dụ "làm tiếp đi", "thêm chức năng lọc đơn", "web bị lỗi khi bấm lưu") thì hiểu là lệnh tương ứng và làm theo skill đó.

## Luật cứng (hook tự động ép buộc)

- **Unit test bắt buộc:** sửa file code mà chưa có file test thì hook nhắc ngay.
- **Không commit khi code chưa qua `pm verify`:** hook chặn `git commit`.
- **Sửa giao diện phải nạp skill `frontend-design:frontend-design` trước:** hook chặn nếu chưa nạp.
- **Lệnh phá dữ liệu phải hỏi lại PO:** `docker compose down -v`, `rm -rf`, `git push --force`, `DROP TABLE`…
- **Stack cố định:** Docker, FastAPI (Python), PostgreSQL, Redis, Next.js + Tailwind + TypeScript + Bun, Traefik, Hurl, Playwright. Backend theo kiến trúc Hexagonal.
- Tên hàm, biến, class bằng tiếng Anh. Tài liệu và giao diện bằng tiếng Việt.

## Thông tin dự án

- Tài liệu yêu cầu: `docs/PRD.md`
- Kiến trúc: `docs/ARCHITECTURE.md`
- Thiết kế: `docs/DESIGN.md`
- Quyết định: `docs/decisions/`
- Bảng việc: `docs/BOARD.md` (tự sinh), dữ liệu ở `.pm/`
- Trạng thái hiện tại được nạp tự động mỗi đầu phiên (dòng `[pm]`).
