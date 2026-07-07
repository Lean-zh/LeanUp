#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-${VERSION:-v4.30.0}}"
SERVER="${SERVER:-http://127.0.0.1:8765}"
LEANUP_HOME="${LEANUP_HOME:-$HOME/.leanup}"
LEANUP_CACHE_DIR="${LEANUP_CACHE_DIR:-$LEANUP_HOME/cache}"
ROOT="${ROOT:-$LEANUP_CACHE_DIR/serve}"

paths=(
  "elan/base/elan-base.tar.gz"
  "lean/$VERSION/toolchain.tar.gz"
  "mathlib/$VERSION/mathlib-lake.tar.gz"
)

for path in "${paths[@]}"; do
  file="$ROOT/$path"
  test -s "$file"
  printf 'local %s %s bytes\n' "$path" "$(stat -c '%s' "$file")"
  curl --noproxy '*' --fail -sSI "$SERVER/$path" \
    | awk -v p="$path" 'NR==1 {printf "http %s %s ", p, $0} tolower($1)=="content-length:" {print $0}'
done

tar -tzf "$ROOT/lean/$VERSION/toolchain.tar.gz" | sed -n '1,3p' >/dev/null
tar -tzf "$ROOT/mathlib/$VERSION/mathlib-lake.tar.gz" | sed -n '1,3p' >/dev/null
echo "provider asset verification ok for $VERSION via $SERVER"
