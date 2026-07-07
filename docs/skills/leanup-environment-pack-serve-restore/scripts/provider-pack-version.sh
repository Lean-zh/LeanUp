#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-${VERSION:-v4.30.0}}"
LEANUP="${LEANUP:-leanup}"
ELAN_HOME="${ELAN_HOME:-$HOME/.elan}"
PROJECT_ROOT="${PROJECT_ROOT:-$HOME/leanup-provider-projects}"
SERVE_ROOT="${SERVE_ROOT:-$HOME/.leanup/cache/serve}"
LOG="${LOG:-$HOME/.leanup/logs/provider-pack-${VERSION}.log}"
PACK_WORK_ROOT="${PACK_WORK_ROOT:-${TMPDIR:-/tmp}}"
PACK_WORK_DIR=""

cleanup_pack_work() {
  if [ -n "$PACK_WORK_DIR" ] && [ -d "$PACK_WORK_DIR" ]; then
    rm -rf "$PACK_WORK_DIR"
  fi
}
trap cleanup_pack_work EXIT

export PATH="$ELAN_HOME/bin:$PATH"
export TMPDIR="${TMPDIR:-/tmp}"
export TMP_DIR="${TMP_DIR:-$TMPDIR}"

mkdir -p "$PROJECT_ROOT" "$SERVE_ROOT" "$(dirname "$LOG")"
{
  echo "[$(date -Is)] provider pack start version=$VERSION host=$(hostname)"
  echo "leanup=$LEANUP"
  echo "elan_home=$ELAN_HOME"
  echo "project_root=$PROJECT_ROOT"
  echo "serve_root=$SERVE_ROOT"
  echo "tmpdir=$TMPDIR tmp_dir=$TMP_DIR"
  command -v pigz || true
  nproc || true
} | tee -a "$LOG"

"$LEANUP" lean check "$VERSION" --elan-home "$ELAN_HOME" | tee -a "$LOG"
"$LEANUP" elan pack --elan-home "$ELAN_HOME" | tee -a "$LOG"
"$LEANUP" lean pack "$VERSION" --elan-home "$ELAN_HOME" | tee -a "$LOG"

# Optional provider workspace for local use. It is not the portable pack source.
SOURCE_DIR="$PROJECT_ROOT/$VERSION"
"$LEANUP" mathlib setup "$SOURCE_DIR" \
  --lean-version "$VERSION" \
  --name MathlibProvider \
  --dependency-mode symlink \
  --force \
  -I 2>&1 | tee -a "$LOG"

# Portable .lake archives must come from a copy-mode source. Keep it temporary.
mkdir -p "$PACK_WORK_ROOT"
PACK_WORK_DIR=$(mktemp -d "$PACK_WORK_ROOT/leanup-pack-${VERSION}.XXXXXX")
PACK_SOURCE_DIR="$PACK_WORK_DIR/MathlibPack"
"$LEANUP" mathlib setup "$PACK_SOURCE_DIR" \
  --lean-version "$VERSION" \
  --name MathlibPack \
  --dependency-mode copy \
  --force \
  -I 2>&1 | tee -a "$LOG"

"$LEANUP" mathlib check "$VERSION" --source "$PACK_SOURCE_DIR" | tee -a "$LOG"
"$LEANUP" mathlib pack "$VERSION" --source "$PACK_SOURCE_DIR" | tee -a "$LOG"

for required in \
  "$SERVE_ROOT/elan/base/elan-base.tar.gz" \
  "$SERVE_ROOT/lean/$VERSION/toolchain.tar.gz" \
  "$SERVE_ROOT/mathlib/$VERSION/mathlib-lake.tar.gz"; do
  test -s "$required"
done

find "$SERVE_ROOT" -maxdepth 5 -type f -printf '%p %s bytes\n' | sort | tee -a "$LOG"
echo "[$(date -Is)] provider pack done version=$VERSION" | tee -a "$LOG"
