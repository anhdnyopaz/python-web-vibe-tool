#!/usr/bin/env bash
# (chạy TRÊN server, do deploy.sh gọi) — backup, chuyển symlink current, khởi động bản mới.
set -euo pipefail
app_dir="$1"; version="$2"
cd "${app_dir}"
env_file="${app_dir}/shared/.env.prod"
slug="$(grep '^APP_SLUG=' "${env_file}" | cut -d= -f2)"

if [ -L current ]; then
  readlink current > previous
  bash "current/deploy/backup.sh" "${slug}" "${app_dir}/backups"
fi

ln -sfn "releases/${version}" current.new && mv -Tf current.new current
cd current
docker compose -f docker-compose.prod.yml -f deploy/vps/compose.vps.yml --env-file "${env_file}" \
  up -d --build --wait --remove-orphans

# backup tự động 3h sáng mỗi ngày
cron_line="0 3 * * * bash ${app_dir}/current/deploy/backup.sh ${slug} ${app_dir}/backups >/dev/null 2>&1"
( crontab -l 2>/dev/null | grep -vF "${app_dir}/current/deploy/backup.sh"; echo "${cron_line}" ) | crontab -

# giữ 5 bản phát hành gần nhất
ls -1dt "${app_dir}"/releases/*/ | tail -n +6 | xargs -r rm -rf
docker image prune -f >/dev/null
echo "Bản ${version} đang chạy."
