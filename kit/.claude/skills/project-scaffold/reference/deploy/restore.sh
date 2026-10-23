#!/usr/bin/env bash
# KHÔI PHỤC database từ file backup — GHI ĐÈ dữ liệu hiện tại. Chỉ chạy khi Product Owner đồng ý.
#   deploy/restore.sh <app-slug> <file.sql.gz>
set -euo pipefail
slug="${1:?Thiếu app slug}"; file="${2:?Thiếu file backup}"
gunzip -c "${file}" | docker exec -i "${slug}-db-1" psql -U app -d app -v ON_ERROR_STOP=1 >/dev/null
echo "Đã khôi phục từ ${file}"
