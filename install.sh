#!/usr/bin/env bash
# Cài TechLead Kit vào một thư mục dự án.
#   ./install.sh ~/Projects/shop-hoa            # dự án mới (thư mục chưa có hoặc trống)
#   ./install.sh ~/Projects/shop-hoa --update   # cập nhật kit cho dự án đã cài (giữ dữ liệu .pm, docs, code)
# Cài từ xa:
#   curl -fsSL https://raw.githubusercontent.com/anhdnyopaz/python-web-vibe-tool/main/install.sh | bash -s -- ~/Projects/shop-hoa
set -euo pipefail

REPO_URL="https://github.com/anhdnyopaz/python-web-vibe-tool.git"
target="${1:-}"
mode="${2:-}"
if [ -z "$target" ]; then
  echo "Cách dùng: ./install.sh <thư-mục-dự-án> [--update]"; exit 1
fi

say() { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }

# --- tìm bộ kit (cạnh script, hoặc tải về) ---
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || pwd)"
kit_dir="$script_dir/kit"
if [ ! -d "$kit_dir/.claude" ]; then
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  say "Tải TechLead Kit từ $REPO_URL"
  git clone --depth 1 --quiet "$REPO_URL" "$tmp/kit-repo"
  kit_dir="$tmp/kit-repo/kit"
fi

# --- kiểm tra công cụ cần có ---
missing=0
for tool in git python3; do
  command -v "$tool" >/dev/null 2>&1 || { warn "Thiếu '$tool'"; missing=1; }
done
if ! command -v docker >/dev/null 2>&1; then
  warn "Chưa có Docker — cài Docker Desktop: https://www.docker.com/products/docker-desktop/"
fi
if ! command -v claude >/dev/null 2>&1; then
  warn "Chưa có Claude Code — cài theo https://code.claude.com/docs (hoặc dùng tab Code trong ứng dụng Claude desktop)"
fi
[ "$missing" = 0 ] || { echo "Cài các công cụ còn thiếu rồi chạy lại."; exit 1; }
python3 - <<'PY' || { echo "Cần Python 3.9 trở lên"; exit 1; }
import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)
PY

mkdir -p "$target"
target="$(cd "$target" && pwd)"

if [ -f "$target/.claude/tools/pm.py" ] && [ "$mode" != "--update" ]; then
  echo "Thư mục đã cài TechLead Kit. Dùng --update để cập nhật."; exit 1
fi
if [ "$mode" != "--update" ] && [ -n "$(ls -A "$target" 2>/dev/null | grep -v '^\.git$' || true)" ]; then
  warn "Thư mục không trống — kit chỉ thêm .claude/ và CLAUDE.md, không đụng file khác."
fi

say "Chép cấu hình agent, skill, hook, công cụ vào $target/.claude"
mkdir -p "$target/.claude"
for part in agents skills hooks tools; do
  rm -rf "$target/.claude/$part"
  cp -R "$kit_dir/.claude/$part" "$target/.claude/$part"
done
find "$target/.claude" -name '__pycache__' -type d -prune -exec rm -rf {} +
if [ -f "$target/.claude/settings.json" ] && [ "$mode" = "--update" ]; then
  cp "$target/.claude/settings.json" "$target/.claude/settings.json.bak"
  warn "Đã sao lưu settings.json cũ thành settings.json.bak"
fi
cp "$kit_dir/.claude/settings.json" "$target/.claude/settings.json"

if [ -f "$target/CLAUDE.md" ] && ! grep -q "TechLead Kit" "$target/CLAUDE.md"; then
  cp "$target/CLAUDE.md" "$target/CLAUDE.md.bak"
  warn "Đã sao lưu CLAUDE.md cũ thành CLAUDE.md.bak"
fi
cp "$kit_dir/CLAUDE.md" "$target/CLAUDE.md"
chmod +x "$target"/.claude/hooks/*.py "$target"/.claude/tools/pm.py

if [ ! -d "$target/.git" ]; then
  say "Khởi tạo git"
  git -C "$target" init -q -b main
fi

cat <<MSG

✅ Đã cài TechLead Kit vào: $target

Bước tiếp theo:
  1. Mở Docker Desktop (chờ biểu tượng cá voi đứng yên).
  2. Mở Claude Code trong thư mục dự án:
       cd "$target" && claude
     (hoặc mở thư mục này trong tab Code của ứng dụng Claude desktop)
  3. Cài plugin thiết kế nếu Claude Code hỏi (frontend-design) — bấm đồng ý.
  4. Gõ:  /kickoff   rồi kể ý tưởng sản phẩm của bạn.

MSG
