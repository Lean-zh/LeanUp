#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-${VERSION:-v4.30.0}}"
SERVER="${SERVER:?Set SERVER to the provider URL, for example http://PROVIDER_HOST:8765}"
LEANUP="${LEANUP:-leanup}"
ELAN_HOME="${ELAN_HOME:-$HOME/.elan}"
LEANUP_HOME="${LEANUP_HOME:-$HOME/.leanup}"
LEANUP_CACHE_DIR="${LEANUP_CACHE_DIR:-$LEANUP_HOME/cache}"
CHECK_ROOT="${CHECK_ROOT:-$HOME/leanup-check-$VERSION}"
TMPDIR="${TMPDIR:-$HOME/.cache/leanup-runtime-tmp}"

export LEANUP_HOME LEANUP_CACHE_DIR
export PATH="$ELAN_HOME/bin:$PATH"
export TMPDIR
mkdir -p "$TMPDIR"

provider_host=$(printf '%s\n' "$SERVER" | sed -E 's#^[a-zA-Z]+://([^/:]+).*#\1#')
export no_proxy="$provider_host,127.0.0.1,localhost,${no_proxy:-}"
export NO_PROXY="$no_proxy"

# LeanUp is a normal Python tool prerequisite. The no-public-network boundary
# starts at Lean-related environment restore actions below.
test -x "$(command -v "$LEANUP")"
"$LEANUP" --version

# The provider server is reachable through no_proxy; accidental public-network
# access fails fast.
export http_proxy=http://127.0.0.1:9
export https_proxy=http://127.0.0.1:9
export all_proxy=http://127.0.0.1:9

"$LEANUP" init --server "$SERVER"
"$LEANUP" elan get --server "$SERVER"
"$LEANUP" elan unpack --elan-home "$ELAN_HOME"
"$LEANUP" lean get "$VERSION" --server "$SERVER"
"$LEANUP" lean unpack "$VERSION" --elan-home "$ELAN_HOME"
"$LEANUP" elan check --elan-home "$ELAN_HOME"
"$LEANUP" lean check "$VERSION" --elan-home "$ELAN_HOME"

archive="$LEANUP_CACHE_DIR/serve/mathlib/$VERSION/mathlib-lake.tar.gz"
mkdir -p "$(dirname "$archive")"
curl --noproxy "$provider_host,127.0.0.1,localhost" --fail --location \
  --output "$archive.tmp" "$SERVER/mathlib/$VERSION/mathlib-lake.tar.gz"
mv "$archive.tmp" "$archive"

"$LEANUP" mathlib unpack "$VERSION"
rm -rf "$CHECK_ROOT"
"$LEANUP" mathlib setup "$CHECK_ROOT" \
  --lean-version "$VERSION" \
  --name MathlibCheck \
  --dependency-mode symlink \
  --force \
  -I
"$LEANUP" mathlib check "$VERSION" --source "$CHECK_ROOT"

if find "$TMPDIR" -maxdepth 1 -mindepth 1 | grep -q .; then
  echo "unexpected temporary residue in $TMPDIR" >&2
  find "$TMPDIR" -maxdepth 2 -mindepth 1 >&2
  exit 1
fi

echo "lean-related offline restore ok for $VERSION via $SERVER"
