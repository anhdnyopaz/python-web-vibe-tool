#!/usr/bin/env bash
# Chuẩn bị VPS mới (Ubuntu 24.04 / Debian 12). Chạy MỘT LẦN bằng root:
#   ssh -i ~/.ssh/<app>_deploy root@IP 'bash -s' < deploy/vps/setup-server.sh
# Kết quả: user "deploy" (đăng nhập bằng cùng SSH key), Docker, tường lửa, fail2ban,
# tự cập nhật bảo mật, Nginx Proxy Manager tại /opt/npm, mạng docker "proxy".
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "Cần chạy bằng root"; exit 1; }
[ -s /root/.ssh/authorized_keys ] || { echo "root chưa có SSH key — dừng để tránh bị khoá ngoài"; exit 1; }
export DEBIAN_FRONTEND=noninteractive

echo "==> Cập nhật hệ thống"
apt-get update -y
apt-get upgrade -y
apt-get install -y ca-certificates curl ufw fail2ban unattended-upgrades rsync python3 openssl
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "==> Swap 2GB (giúp build trên VPS RAM nhỏ)"
if ! swapon --show | grep -q .; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
  sh /tmp/get-docker.sh
fi
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'JSON'
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
JSON
systemctl enable docker
systemctl restart docker

echo "==> User deploy"
id deploy >/dev/null 2>&1 || adduser --disabled-password --gecos "" deploy
usermod -aG docker deploy
install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
install -m 600 -o deploy -g deploy /root/.ssh/authorized_keys /home/deploy/.ssh/authorized_keys
install -d -m 755 -o deploy -g deploy /opt/apps

echo "==> Tường lửa: chỉ mở 22, 80, 443"
ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
systemctl enable --now fail2ban

echo "==> Nginx Proxy Manager (/opt/npm) — trang quản trị chỉ mở ở 127.0.0.1:81"
docker network inspect proxy >/dev/null 2>&1 || docker network create proxy
mkdir -p /opt/npm/data /opt/npm/letsencrypt
cat > /opt/npm/docker-compose.yml <<'YAML'
services:
  npm:
    image: jc21/nginx-proxy-manager:2.16.0
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "127.0.0.1:81:81"
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt
    networks: [proxy]
networks:
  proxy:
    external: true
YAML
docker compose -f /opt/npm/docker-compose.yml up -d

echo "==> Khoá SSH: tắt đăng nhập mật khẩu và đăng nhập root"
cat > /etc/ssh/sshd_config.d/99-hardening.conf <<'CONF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
CONF
sshd -t
systemctl reload ssh 2>/dev/null || systemctl reload sshd

echo "✅ Xong. Từ giờ đăng nhập bằng: ssh deploy@<IP> (cùng SSH key)."
