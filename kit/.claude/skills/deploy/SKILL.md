---
name: deploy
description: Đưa một phiên bản đã chốt lên môi trường chạy thật (VPS hoặc Cloudflare Tunnel), có backup trước, kiểm tra sau và tự quay lại bản cũ nếu lỗi. Dùng khi người dùng muốn deploy/đưa bản mới lên mạng hoặc gõ /deploy.
argument-hint: "[phiên bản, mặc định tag mới nhất]"
---

# /deploy — Đưa phiên bản lên chạy thật

Đọc `.claude/skills/deploy-playbook/SKILL.md` (mục A hoặc B tuỳ `DEPLOY_TARGET` trong `.deploy/config`).

## 1. Điều kiện (thiếu thì dừng và hướng dẫn)
- Có `.deploy/config`. Chưa có thì cần `/deploy-setup`.
- `git status` sạch, đang ở `main`.
- Có tag phiên bản: `git describe --tags --abbrev=0`. Chưa có tag thì cần `/release`.
- `pm status`: lần kiểm tra gần nhất đạt và code không đổi sau đó. Nếu không, chạy `/test` trước.

## 2. Xác nhận với PO (AskUserQuestion)
"Đưa phiên bản <vX.Y.Z> lên <domain> (<VPS|máy này qua Cloudflare Tunnel>)? Dữ liệu sẽ được backup trước." Chỉ tiếp tục khi PO đồng ý.

## 3. Chạy
- **VPS:**
  1. `deploy/vps/deploy.sh <tag>` (timeout 600000).
  2. Lần đầu: chạy thêm bước Nginx Proxy Manager (`npm_proxy.py`) theo mục B3 của playbook.
- **Tunnel:**
  1. Backup.
  2. `git checkout <tag> && make prod-tunnel-up; git checkout main`.
  3. Health check bằng Hurl.
  4. `pm deploy-log`.

## 4. Báo PO
- **Thành công:** link https, những gì mới (từ CHANGELOG), "đã backup dữ liệu lúc …".
- **Thất bại:** hệ thống đã tự quay lại bản cũ (nếu có). Tóm tắt nguyên nhân từ log. Đề nghị giao TechLead sửa (`/fix`).
