#!/usr/bin/env bash
# Tạo .deploy/.env.prod với mật khẩu ngẫu nhiên. Không ghi đè nếu đã có.
set -euo pipefail
slug="${1:?Cách dùng: deploy/init-env.sh <app-slug>}"
mkdir -p .deploy && chmod 700 .deploy
if [ -f .deploy/.env.prod ]; then
  echo ".deploy/.env.prod đã tồn tại — giữ nguyên."
  exit 0
fi
umask 077
cat > .deploy/.env.prod <<ENV
APP_SLUG=${slug}
# cổng local của bản production (khác 8080 của bản dev để chạy song song được)
APP_PORT=8081
POSTGRES_PASSWORD=$(openssl rand -hex 24)
CLOUDFLARE_TUNNEL_TOKEN=
ENV
echo "Đã tạo .deploy/.env.prod (mật khẩu ngẫu nhiên, chỉ nằm trên máy này)."
