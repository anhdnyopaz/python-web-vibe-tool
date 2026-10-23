---
name: deploy-setup
description: Trình hướng dẫn từng bước thiết lập nơi chạy thật — Cloudflare Tunnel (chạy trên máy của mình) hoặc VPS + Nginx Proxy Manager (thuê máy chủ, đưa SSH key cho agent). Dùng khi người dùng muốn đưa app lên mạng lần đầu hoặc gõ /deploy-setup.
---

# /deploy-setup — Thiết lập nơi chạy thật

Đọc toàn bộ `.claude/skills/deploy-playbook/SKILL.md` trước.

## 1. Giúp PO chọn (AskUserQuestion)

- **VPS + Nginx Proxy Manager (khuyên dùng):**
  - Thuê máy chủ khoảng 120–250k/tháng.
  - Chạy 24/7, ổn định, có HTTPS.
  - PO cần: tài khoản nhà cung cấp VPS và một domain.
- **Cloudflare Tunnel:**
  - Miễn phí, chạy ngay trên máy của PO, không cần mở cổng mạng.
  - Máy phải luôn bật.
  - PO cần: domain quản lý trên Cloudflare.

Chỉ muốn cho khách xem tạm bản đang làm thì dùng `/preview`, không cần bước này.

## 2. Thu thập thông tin

Tên miền muốn dùng (ví dụ `app.tencongty.vn`) và email nhận thông báo SSL. Chưa có domain thì gợi ý nơi mua (Mắt Bão, PA Việt Nam, Namecheap, Cloudflare Registrar).

## 3. Dẫn PO từng bước

Theo mục A hoặc B của playbook:
- Mỗi lần chỉ đưa **một** bước nhỏ, kèm chỗ cần bấm. Chờ PO báo xong (AskUserQuestion: "Xong rồi" / "Bị kẹt").
- Phần nào agent tự làm được (tạo SSH key, chạy script cài server, ghi file cấu hình) thì tự làm. Bước nguy hiểm thì hỏi xác nhận trước.
- **Không bao giờ** yêu cầu PO gửi mật khẩu root hay private key. Chỉ cần public key, IP và token tunnel.

## 4. Kiểm tra cuối

- **VPS:** `ssh deploy@IP docker ps` chạy được.
- **Tunnel:** `.deploy/.env.prod` có token.

Ghi `.deploy/config`. Báo PO đã sẵn sàng, gợi ý `/release` rồi `/deploy`.
