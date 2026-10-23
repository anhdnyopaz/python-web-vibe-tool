# TechLead Kit cho Claude Code

Bộ cấu hình giúp **người không biết lập trình** dùng Claude Code để làm ra một sản phẩm web theo **quy trình chuyên nghiệp**. Bạn đóng vai **Product Owner**: nói mình muốn gì bằng lời thường. Một **TechLead ảo** (sub agent) lập kế hoạch, viết code, viết test và kiểm tra chất lượng. Các quy định quan trọng được **công cụ tự động ép buộc**, không phụ thuộc vào việc AI có "nhớ" hay không.

> Đây không phải một ứng dụng. Kit gồm agent, skill (lệnh `/...`), hook và một công cụ quản lý dự án nhỏ. Kit được cài vào thư mục dự án của bạn, rồi TechLead sẽ dựng code dự án từ mẫu chuẩn đã kiểm chứng.

## Bạn nhận được gì

| Thành phần | Vai trò |
|---|---|
| **Sub agent `techlead`** | Kỹ sư trưởng: phân tích yêu cầu thành task có tiêu chí chấp nhận, viết test trước, code, tự review, commit theo chuẩn |
| **13 lệnh cho người dùng** | `/kickoff`, `/feature`, `/next`, `/fix`, `/progress`, `/board`, `/demo`, `/preview`, `/test`, `/release`, `/deploy-setup`, `/deploy`, `/server` |
| **Công cụ `pm`** | Quản lý task, tiêu chí chấp nhận, cổng kiểm tra chất lượng, câu hỏi cho PO, yêu cầu mới, quyết định kỹ thuật (ADR), CHANGELOG, lịch sử deploy |
| **Bảng điều hành web** (`/board`) | Xem tiến độ, trả lời câu hỏi của TechLead, gửi yêu cầu, nghiệm thu ngay trên trình duyệt |
| **Hook bảo vệ** | Chặn commit khi chưa test; nhắc viết unit test; bắt buộc dùng skill thiết kế khi làm giao diện; hỏi lại trước lệnh xoá dữ liệu |
| **Mẫu dự án chuẩn** | Backend Hexagonal có module mẫu, frontend, gateway, đủ 4 tầng test, script deploy |

## Stack cố định

| Phần | Công nghệ |
|---|---|
| Đóng gói | Docker + Docker Compose (máy chỉ cần Docker Desktop) |
| API Gateway | Traefik: `/api/*` → backend, còn lại → frontend |
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic, **kiến trúc Hexagonal** (controller → usecase → module service/repository, mỗi tầng qua interface) |
| Dữ liệu | PostgreSQL 17 · Redis 8 |
| Frontend | Next.js 16 · TypeScript · Tailwind CSS 4 · Bun, **bắt buộc dùng skill `frontend-design`** |
| Kiểm thử | **Unit test bắt buộc** (pytest ≥ 80%, bun test ≥ 70%) · Hurl (API) · Playwright (giao diện, desktop + mobile) |
| Chạy thật | Cloudflare Tunnel **hoặc** VPS + Nginx Proxy Manager |
| Xem online khi đang dev | Cloudflare Quick Tunnel (miễn phí, không cần tài khoản) hoặc ngrok |

## Cài đặt

**Cần có:**
- [Claude Code](https://code.claude.com/docs): bản CLI, hoặc tab Code trong ứng dụng Claude desktop
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git
- Python 3.9+ (macOS đã có sẵn)

```bash
# Cách 1: cài từ xa
curl -fsSL https://raw.githubusercontent.com/anhdnyopaz/python-web-vibe-tool/main/install.sh | bash -s -- ~/Projects/ten-du-an

# Cách 2: clone về rồi cài
git clone https://github.com/anhdnyopaz/python-web-vibe-tool.git
./python-web-vibe-tool/install.sh ~/Projects/ten-du-an
```

Sau đó:

```bash
cd ~/Projects/ten-du-an
claude
```

Gõ `/kickoff` rồi kể ý tưởng của bạn. Khi Claude Code hỏi cài plugin **frontend-design**, hãy đồng ý.

Cập nhật kit cho dự án đã cài: `./install.sh ~/Projects/ten-du-an --update`. Lệnh này giữ nguyên code, dữ liệu `.pm/` và tài liệu.

## Quy trình làm việc

```
 /kickoff ──► phỏng vấn ──► PRD ──► TechLead dựng khung + design system + kế hoạch task
                                              │
      ┌───────────────────────────────────────┘
      ▼
   /next ──► TechLead: start task ─► test trước ─► code ─► pm verify (lint, unit, API, UI)
      ▲                                                          │ đạt
      │                                                          ▼
      │      PO thử theo hướng dẫn ◄── báo cáo lời thường ◄── tự review ─► submit ─► commit ─► merge
      │            │
      └── /feature, /fix, hoặc gửi yêu cầu trên /board
                   │
   /release ──► /deploy-setup (một lần) ──► /deploy ──► /server (log, backup, rollback)
```

Mỗi task chỉ được tính là **xong** khi:
1. Mọi tiêu chí chấp nhận (Given/When/Then) đều có test chứng minh.
2. `pm verify` đạt **sau** lần sửa code cuối cùng: lint + luật kiến trúc + unit test, cộng Hurl nếu có API, cộng Playwright nếu có giao diện.

Bước nghiệm thu bởi PO là **tuỳ chọn**. Bật bằng `"require_acceptance": true` trong `.pm/config.json`.

## Những gì được ép buộc tự động

| Quy định | Cơ chế |
|---|---|
| Unit test bắt buộc | Hook `require_tests.py` nhắc ngay khi file code chưa có test. Ngưỡng coverage làm `make test-unit` thất bại. `pm submit` từ chối nếu chưa verify |
| Không commit code chưa kiểm tra | Hook `guard_bash.py` chặn `git commit` khi mã nguồn khác với lần `pm verify` đạt gần nhất (so dấu vân tay nội dung file). Chặn luôn `--no-verify` |
| Kiến trúc Hexagonal | `import-linter` với 5 hợp đồng phụ thuộc, cộng test kiến trúc (mỗi module có `IxxxService`/`IxxxRepository`, mọi usecase kế thừa interface) |
| Kiến trúc frontend | Test kiến trúc: component chỉ dùng interface qua `useApi()`, không gọi `fetch` trực tiếp |
| Thiết kế qua skill frontend-design | Hook `require_design.py` từ chối sửa `.tsx`/`.css` nếu skill chưa được nạp trong phiên (đọc cả transcript của sub agent) |
| An toàn dữ liệu | `docker compose down -v`, `rm -rf`, `git push --force`, `git reset --hard`, `DROP TABLE`… đều phải được bạn xác nhận, kể cả khi chạy qua `ssh` |
| Mỗi lúc một việc | `pm start` giới hạn 1 task đang làm (WIP limit) và kiểm tra thứ tự phụ thuộc |

## Bảng điều hành (`/board`)

Mở tại `http://localhost:4000`, chạy bằng Python có sẵn, không cài thêm gì.
- **Việc cần bạn:** câu hỏi TechLead đang chờ (trả lời ngay trên trang), việc chờ nghiệm thu (Chấp nhận / Trả lại kèm lý do), việc bị chặn.
- **Kanban:** Cần làm / Đang làm / Bị chặn / Đã xong. Bấm vào việc để xem tiêu chí chấp nhận và kết quả kiểm tra.
- **Gửi yêu cầu:** "Muốn thêm…" hoặc "Báo lỗi…" bằng lời thường. TechLead xử lý ở lần `/next` sau.
- **Link nhanh:** ứng dụng ở máy, link chia sẻ online, bản chạy thật, lịch sử deploy, nút sao chép lệnh.

Trang chỉ nghe ở `127.0.0.1`. Thao tác ghi cần token sinh ngẫu nhiên mỗi lần chạy, nên trang web khác không giả mạo được.

## Đưa lên Internet

| Nhu cầu | Cách | Lệnh |
|---|---|---|
| Cho khách xem tạm bản đang làm | Cloudflare Quick Tunnel (miễn phí, không cần tài khoản), hoặc ngrok (link cố định) | `/preview` |
| Chạy thật, rẻ, máy luôn bật | **Cloudflare Tunnel**: chạy trên máy của bạn, không cần mở cổng router | `/deploy-setup` |
| Chạy thật, ổn định 24/7 (khuyên dùng) | **VPS + Nginx Proxy Manager**: agent tạo SSH key riêng, bạn chỉ dán *public key* khi tạo VPS | `/deploy-setup` |

Với VPS, script tự làm các việc sau:
- tạo user `deploy`
- cài Docker, bật tường lửa (chỉ 22/80/443), fail2ban, tự cập nhật bảo mật
- tắt đăng nhập root và mật khẩu
- cài Nginx Proxy Manager, tạo proxy host và xin SSL Let's Encrypt qua API

Mỗi lần deploy đều backup database trước và kiểm tra health sau. Nếu lỗi, hệ thống tự quay lại bản cũ.

## Cấu trúc repo

```
install.sh                 Trình cài đặt
kit/                       Những gì được chép vào dự án của bạn
├── CLAUDE.md              Luật cho luồng chính (điều phối, nói tiếng Việt dễ hiểu)
└── .claude/
    ├── agents/techlead.md
    ├── skills/            13 lệnh cho người dùng + 6 skill kiến thức (stack, hexagonal, frontend, testing,
    │                      deploy-playbook, project-scaffold kèm mẫu dự án ở reference/)
    ├── hooks/             guard_bash, require_tests, require_design, session_start
    ├── tools/pm.py        Công cụ quản lý dự án + dashboard.html
    └── settings.json      Khai báo hook, quyền, plugin frontend-design
tests/                     Unit test của pm.py và các hook
```

## Phát triển kit

```bash
python3 -m unittest discover -s tests -v      # 46 test cho pm.py và hook (Python 3.9+)
```

Mẫu dự án (`kit/.claude/skills/project-scaffold/reference/`) được kiểm chứng bằng cách chạy `make up` rồi `pm verify --all`. Mọi gate phải đạt.
