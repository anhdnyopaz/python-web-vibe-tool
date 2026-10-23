#!/usr/bin/env bash
# Deploy một phiên bản (git tag) lên VPS. Chạy trên máy dev:
#   deploy/vps/deploy.sh v0.2.0
# Các bước: kiểm tra -> upload code -> backup DB -> chạy bản mới -> kiểm tra sống -> lỗi thì rollback.
set -euo pipefail
version="${1:?Cách dùng: deploy/vps/deploy.sh <git-tag>}"
[ -f .deploy/config ] || { echo "Thiếu .deploy/config — chạy /deploy-setup"; exit 1; }
[ -f .deploy/.env.prod ] || { echo "Thiếu .deploy/.env.prod — chạy deploy/init-env.sh"; exit 1; }
# shellcheck disable=SC1091
source .deploy/config
key="${SSH_KEY/#\~/$HOME}"
remote="${VPS_USER:-deploy}@${VPS_HOST}"
ssh_cmd=(ssh -i "$key" -o StrictHostKeyChecking=accept-new -o BatchMode=yes "$remote")
app_dir="/opt/apps/${APP_SLUG}"
pm() { python3 .claude/tools/pm.py "$@" >/dev/null 2>&1 || true; }

git rev-parse -q --verify "refs/tags/${version}" >/dev/null || { echo "Không có tag ${version}"; exit 1; }
[ -z "$(git status --porcelain)" ] || { echo "Còn thay đổi chưa commit — commit trước khi deploy"; exit 1; }

echo "==> Upload ${version} lên ${VPS_HOST}"
"${ssh_cmd[@]}" "mkdir -p ${app_dir}/releases/${version} ${app_dir}/shared ${app_dir}/backups && chmod 700 ${app_dir}/shared"
git archive --format=tar "${version}" | "${ssh_cmd[@]}" "tar -x -C ${app_dir}/releases/${version}"
"${ssh_cmd[@]}" "umask 077 && cat > ${app_dir}/shared/.env.prod" < .deploy/.env.prod

echo "==> Backup database + chạy bản mới"
if ! "${ssh_cmd[@]}" "bash -s -- ${app_dir} ${version}" < deploy/vps/remote-release.sh; then
  echo "❌ Bản mới không khởi động được — quay lại bản cũ"
  "${ssh_cmd[@]}" "bash -s -- ${app_dir}" < deploy/vps/remote-rollback.sh || true
  pm deploy-log --version "${version}" --target vps --result rolled_back --note "khởi động lỗi"
  exit 1
fi

echo "==> Kiểm tra https://${DOMAIN}"
sleep 3
if ! docker run --rm -v "$PWD/tests/api:/tests:ro" ghcr.io/orange-opensource/hurl:8.0.1 \
     --test --retry 5 --retry-interval 3000 --variable "base_url=https://${DOMAIN}" /tests/health.hurl; then
  echo "❌ Kiểm tra sau deploy thất bại — quay lại bản cũ"
  "${ssh_cmd[@]}" "bash -s -- ${app_dir}" < deploy/vps/remote-rollback.sh || true
  pm deploy-log --version "${version}" --target vps --result rolled_back --note "health check thất bại"
  exit 1
fi

pm deploy-log --version "${version}" --target vps --result success
pm link production "https://${DOMAIN}"
echo "✅ Đã deploy ${version}: https://${DOMAIN}"
