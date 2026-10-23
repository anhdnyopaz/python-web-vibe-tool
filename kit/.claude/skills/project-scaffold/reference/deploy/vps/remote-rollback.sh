#!/usr/bin/env bash
# (chạy TRÊN server) — quay về bản phát hành trước đó. Dữ liệu DB giữ nguyên;
# nếu cần khôi phục dữ liệu dùng deploy/restore.sh với file backup.
set -euo pipefail
app_dir="$1"
cd "${app_dir}"
[ -s previous ] || { echo "Không có bản trước để quay lại"; exit 1; }
target="$(cat previous)"
ln -sfn "${target}" current.new && mv -Tf current.new current
cd current
docker compose -f docker-compose.prod.yml -f deploy/vps/compose.vps.yml --env-file "${app_dir}/shared/.env.prod" \
  up -d --build --wait --remove-orphans
echo "Đã quay lại ${target}."
