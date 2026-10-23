---
name: preview
description: Tạo link công khai để người khác xem bản đang phát triển trên máy (Cloudflare Quick Tunnel miễn phí, hoặc ngrok), hoặc tắt link. Dùng khi người dùng muốn gửi link cho khách/đồng nghiệp xem online, hoặc gõ /preview.
argument-hint: "[stop | ngrok]"
---

# /preview — Link xem online bản đang làm

Tham số: $ARGUMENTS. Đọc mục "0. Chia sẻ link bản dev" trong `.claude/skills/deploy-playbook/SKILL.md`.

- **`stop`:** `make share-stop`, báo link đã tắt.
- **`ngrok`:**
  - Chưa có `NGROK_AUTHTOKEN` trong `.env`: hướng dẫn PO đăng ký https://dashboard.ngrok.com/signup, copy **Authtoken**, lấy domain tĩnh miễn phí ở mục Domains. Ghi vào `.env` (không in token ra).
  - Sau đó `make share-ngrok`.
- **Mặc định:**
  1. Đảm bảo app đang chạy (`make up` nếu cần).
  2. Chạy `make share`.
  3. Đưa link cho PO.

Luôn nhắc 3 điều:
1. Ai có link đều xem được. Đừng nhập dữ liệu thật.
2. Link tắt khi chạy `/preview stop` hoặc tắt máy. Link Cloudflare đổi mỗi lần bật.
3. Đây là bản đang làm. Muốn bản chạy ổn định 24/7 thì dùng `/deploy-setup`.
