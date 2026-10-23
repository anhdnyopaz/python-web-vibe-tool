#!/usr/bin/env bash
# Backup Postgres ra file .sql.gz, giữ 7 bản mới nhất. Dùng được cả trên VPS lẫn máy chạy tunnel.
#   deploy/backup.sh <app-slug> <thư-mục-backup>
set -euo pipefail
slug="${1:?Thiếu app slug}"; dir="${2:?Thiếu thư mục backup}"
container="${slug}-db-1"
mkdir -p "${dir}"
if ! docker ps --format '{{.Names}}' | grep -qx "${container}"; then
  echo "Database ${container} chưa chạy — bỏ qua backup"; exit 0
fi
file="${dir}/db-$(date +%Y%m%d-%H%M%S).sql.gz"
docker exec "${container}" pg_dump -U app --clean --if-exists app | gzip > "${file}"
ls -1t "${dir}"/db-*.sql.gz | tail -n +8 | xargs -r rm -f
echo "Đã backup: ${file}"
