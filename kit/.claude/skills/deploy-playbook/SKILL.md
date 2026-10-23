---
name: deploy-playbook
description: Hướng dẫn chi tiết đưa ứng dụng lên Internet — chia sẻ link bản dev (Cloudflare Quick Tunnel/ngrok), cơ chế A Cloudflare Tunnel, cơ chế B VPS + Nginx Proxy Manager qua SSH key, backup/khôi phục/rollback và xử lý sự cố. Dùng cho /preview, /deploy-setup, /deploy, /server.
user-invocable: false
---

# Nguyên tắc an toàn

- Deploy là hành động **ra bên ngoài**: luôn xác nhận với PO trước (tên miền, phiên bản, nơi deploy).
- **Bí mật:**
  - `.deploy/` (config, `.env.prod`) và private key `~/.ssh/<app>_deploy` **không bao giờ** được commit, in ra màn hình hay đưa vào báo cáo.
  - Chỉ public key (`.pub`) được phép đưa cho PO dán vào nhà cung cấp VPS.
- **Trước khi deploy:**
  - `main` sạch.
  - `pm verify --all` đạt.
  - Có tag phiên bản (chạy `/release` trước).
- Không chạy `docker compose down -v` hoặc `docker volume rm` trên server. Đó là dữ liệu thật của khách hàng.

---

# 0. Chia sẻ link bản dev (đang code ở máy, muốn khách xem online)

| Cách | Ưu điểm | Hạn chế | Lệnh |
|---|---|---|---|
| **Cloudflare Quick Tunnel** (mặc định) | Miễn phí, không cần tài khoản, HTTPS, không có trang cảnh báo | Link ngẫu nhiên, đổi mỗi lần bật | `make share` / `make share-stop` |
| ngrok | Có 1 domain tĩnh miễn phí (link không đổi) | Cần tài khoản + authtoken; gói free có trang cảnh báo trước khi vào và giới hạn băng thông | Điền `NGROK_AUTHTOKEN` (và `NGROK_DOMAIN`) vào `.env`, rồi `make share-ngrok` |
| Cloudflare Tunnel có tên (cơ chế A bên dưới) | Domain riêng cố định | Cần domain trên Cloudflare | xem mục A |

Các bước:
1. `make up` phải đang chạy.
2. `make share` in link `https://xxx.trycloudflare.com` và tự lưu vào dashboard (`pm link share`).
3. Nhắc PO:
   - Ai có link đều vào được.
   - Link tắt khi chạy `make share-stop` hoặc tắt máy.
   - Đây là bản dev: dữ liệu thử, có thể chậm.

---

# A. Cloudflare Tunnel — chạy production trên máy của PO (hoặc mini PC), không cần mở cổng router

**Cần:** tài khoản Cloudflare (miễn phí) và một domain đã trỏ nameserver về Cloudflare.

## Hướng dẫn PO (luồng chính đọc từng bước, chờ PO làm xong mới qua bước sau)
1. Đăng ký tại https://dash.cloudflare.com/sign-up.
2. **Add a domain**, nhập domain của bạn, chọn gói **Free**. Cloudflare hiện 2 nameserver; vào trang quản lý domain ở nơi bạn mua (Mắt Bão, PA Việt Nam, Namecheap…) và thay nameserver bằng 2 cái đó. Chờ email "domain is active" (vài phút tới vài giờ).
3. Vào **Zero Trust**, rồi **Networks → Tunnels → Create a tunnel**, chọn **Cloudflared**, đặt tên (ví dụ `shop-hoa`).
4. Ở bước cài đặt, chọn **Docker** và copy đoạn lệnh có `--token eyJ...`. **Chỉ cần gửi phần token** (chuỗi dài bắt đầu bằng `eyJ`).
5. Tab **Public Hostname**:
   - Subdomain: ví dụ `app` (hoặc để trống).
   - Domain: chọn domain của bạn.
   - Service: **HTTP** và URL `traefik:80`.
   - Bấm Save.

## Việc của agent
```bash
deploy/init-env.sh <app-slug>     # tạo .deploy/.env.prod với mật khẩu DB ngẫu nhiên
# ghi token vào .deploy/.env.prod (dòng CLOUDFLARE_TUNNEL_TOKEN=...) bằng công cụ sửa file, KHÔNG echo ra màn hình
printf 'DEPLOY_TARGET=tunnel\nAPP_SLUG=<slug>\nDOMAIN=<host.domain>\n' > .deploy/config
make prod-tunnel-up               # build bản production + cloudflared
docker run --rm -v "$PWD/tests/api:/tests:ro" ghcr.io/orange-opensource/hurl:8.0.1 --test --retry 10 --retry-interval 3000 --variable base_url=https://<host.domain> /tests/health.hurl
python3 .claude/tools/pm.py link production https://<host.domain>
python3 .claude/tools/pm.py deploy-log --version <tag> --target tunnel --result success
```
- **Cập nhật phiên bản:**
  ```bash
  git checkout <tag> && make prod-tunnel-up && git checkout main
  ```
  Trước khi cập nhật, backup: `deploy/backup.sh <slug> .deploy/backups`.
- Lưu ý cho PO: máy phải luôn bật và có mạng. Docker Desktop nên đặt "Start when you sign in".
- **Bản prod và bản dev chạy chung máy:** chúng là 2 project Compose khác nhau (`<slug>` và `COMPOSE_PROJECT_NAME`). Bản prod dùng cổng local `APP_PORT=8081` (do `init-env.sh` đặt), nên không đụng bản dev ở 8080.

---

# B. VPS + Nginx Proxy Manager (khuyên dùng cho sản phẩm thật)

## B1. Hướng dẫn PO đăng ký VPS
- **Cấu hình tối thiểu:** Ubuntu 24.04 LTS, 2 vCPU, 4 GB RAM, 40 GB SSD.
- **Nhà cung cấp:**
  - Quốc tế: Hetzner, DigitalOcean, Vultr.
  - Việt Nam (máy chủ trong nước, thanh toán VNĐ): Viettel IDC, BizFly Cloud, Vietnix.
- Tạo SSH key cho agent **trước** khi tạo VPS. Agent chạy lệnh dưới và đưa PO **nội dung public key**:
  ```bash
  ssh-keygen -t ed25519 -N "" -C "<app-slug>-deploy" -f ~/.ssh/<app-slug>_deploy
  cat ~/.ssh/<app-slug>_deploy.pub     # chỉ public key — an toàn để chia sẻ
  ```
- Khi tạo VPS, chọn **SSH Key**, bấm "Add SSH key", rồi dán public key. Nếu nhà cung cấp chỉ cho mật khẩu root: PO đăng nhập web console một lần, chạy `mkdir -p ~/.ssh && echo '<public key>' >> ~/.ssh/authorized_keys`.
- PO gửi lại **địa chỉ IP** của VPS.
- **Trỏ domain:** tạo bản ghi **A**, tên `app` (hoặc `@`), giá trị là IP VPS. Nếu dùng Cloudflare DNS thì để **DNS only** (mây xám) để Let's Encrypt cấp được chứng chỉ.

## B2. Việc của agent — cài server (một lần)
```bash
ssh -i ~/.ssh/<slug>_deploy -o StrictHostKeyChecking=accept-new root@<IP> 'bash -s' < deploy/vps/setup-server.sh
ssh -i ~/.ssh/<slug>_deploy deploy@<IP> 'docker ps'      # PHẢI chạy được trước khi kết thúc
```
Script sẽ:
- tạo user `deploy`
- cài Docker
- bật tường lửa (chỉ mở 22/80/443), fail2ban và tự cập nhật bảo mật
- thêm 2 GB swap
- cài Nginx Proxy Manager ở `/opt/npm`, trang quản trị chỉ mở ở `127.0.0.1:81`
- tắt đăng nhập root và đăng nhập bằng mật khẩu

Sau đó ghi `.deploy/config` (theo `deploy/config.example`), chạy `deploy/init-env.sh <slug>`.

## B3. Deploy phiên bản
```bash
deploy/vps/deploy.sh vX.Y.Z      # upload → backup DB → chạy bản mới → health check → lỗi thì tự rollback
```
**Lần deploy đầu tiên**, cấu hình Nginx Proxy Manager. Mật khẩu admin tự sinh, lưu vào `.deploy/config`:
```bash
grep -q '^NPM_PASSWORD=' .deploy/config || printf 'NPM_EMAIL=%s\nNPM_PASSWORD=%s\n' "<email PO>" "$(openssl rand -hex 16)" >> .deploy/config
source .deploy/config && ssh -i "${SSH_KEY/#\~/$HOME}" deploy@"$VPS_HOST" \
  "python3 - --domain $DOMAIN --forward-host $APP_SLUG-gateway --email $NPM_EMAIL --password $NPM_PASSWORD --ssl" < deploy/vps/npm_proxy.py
```
- Lệnh này tạo admin NPM (lần đầu), tạo proxy host `<domain>` trỏ tới `<slug>-gateway:80`, xin SSL Let's Encrypt và bật HTTPS.
- Nếu bước SSL lỗi, thường do DNS chưa trỏ đúng hoặc đang bật proxy Cloudflare. Chờ DNS rồi chạy lại; lệnh chạy lại không tạo trùng.
- **Trang quản trị NPM cho PO** (khi cần): `ssh -i ~/.ssh/<slug>_deploy -L 8181:127.0.0.1:81 deploy@<IP>`, rồi mở http://localhost:8181 bằng email/mật khẩu trong `.deploy/config`.

---

# Vận hành (/server)

| Việc | VPS | Tunnel (máy local) |
|---|---|---|
| Trạng thái | `ssh … deploy@IP 'docker ps --format "table {{.Names}}\t{{.Status}}"'` | `docker compose -f docker-compose.prod.yml --env-file .deploy/.env.prod ps` |
| Log | `ssh … deploy@IP 'cd /opt/apps/<slug>/current && docker compose -f docker-compose.prod.yml --env-file ../../shared/.env.prod logs --tail=200 backend'` | `docker compose -f docker-compose.prod.yml --env-file .deploy/.env.prod logs --tail=200` |
| Backup ngay | `ssh … deploy@IP 'bash /opt/apps/<slug>/current/deploy/backup.sh <slug> /opt/apps/<slug>/backups'` | `deploy/backup.sh <slug> .deploy/backups` |
| Danh sách backup | `ssh … deploy@IP 'ls -lh /opt/apps/<slug>/backups'` | `ls -lh .deploy/backups` |
| Rollback code | `ssh … deploy@IP 'bash -s -- /opt/apps/<slug>' < deploy/vps/remote-rollback.sh` | checkout tag cũ, rồi `make prod-tunnel-up` |
| Khôi phục dữ liệu (**ghi đè**, cần PO xác nhận 2 lần) | backup ngay, rồi `ssh … 'bash /opt/apps/<slug>/current/deploy/restore.sh <slug> <file>'` | `deploy/restore.sh <slug> <file>` |

Sau mỗi thao tác deploy/rollback: `pm deploy-log --version … --target … --result success|failed|rolled_back`.

# Xử lý sự cố

| Triệu chứng | Kiểm tra / cách xử lý |
|---|---|
| `Permission denied (publickey)` | Sai key hoặc user. Lần đầu dùng `root`, sau setup dùng `deploy`. Kiểm tra lại public key đã thêm vào VPS chưa. |
| Health check sau deploy thất bại | Xem log backend. Thường do thiếu biến môi trường hoặc lỗi migration. Script đã tự rollback. |
| 502 Bad Gateway từ NPM | Container `<slug>-traefik-1` có đang chạy không? Đã nối mạng `proxy` chưa (`docker network inspect proxy`)? |
| Let's Encrypt lỗi | Bản ghi A phải trỏ đúng IP, tắt proxy Cloudflare (mây xám), cổng 80 phải mở. |
| VPS hết RAM khi build | Swap 2 GB đã bật. Nếu vẫn thiếu, nâng gói VPS lên 4 GB+. |
| Cloudflare Tunnel báo lỗi 1033 | `cloudflared` chưa chạy hoặc token sai. Xem log của service `cloudflared`. |
