#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-${VERSION:-v4.30.0}}"
LEANUP="${LEANUP:-leanup}"
ELAN_HOME="${ELAN_HOME:-$HOME/.elan}"
LEANUP_HOME="${LEANUP_HOME:-$HOME/.leanup}"
LEANUP_CACHE_DIR="${LEANUP_CACHE_DIR:-$LEANUP_HOME/cache}"
CHECK_ROOT="${CHECK_ROOT:-$HOME/leanup-check-$VERSION}"
TMPDIR="${TMPDIR:-$HOME/.cache/leanup-runtime-tmp}"

export LEANUP_HOME LEANUP_CACHE_DIR
export PATH="$ELAN_HOME/bin:$PATH"
export http_proxy=http://127.0.0.1:9
export https_proxy=http://127.0.0.1:9
export all_proxy=http://127.0.0.1:9

"$LEANUP" --version
"$LEANUP" elan check --elan-home "$ELAN_HOME"
"$LEANUP" lean check "$VERSION" --elan-home "$ELAN_HOME"
"$ELAN_HOME/toolchains/leanprover--lean4---$VERSION/bin/lake" --version
"$LEANUP" mathlib check "$VERSION" --source "$CHECK_ROOT"

test -L "$CHECK_ROOT/.lake" || test -d "$CHECK_ROOT/.lake"
if [ -d "$TMPDIR" ] && find "$TMPDIR" -maxdepth 1 -mindepth 1 | grep -q .; then
  echo "unexpected temporary residue in $TMPDIR" >&2
  find "$TMPDIR" -maxdepth 2 -mindepth 1 >&2
  exit 1
fi

echo "consumer verification ok for $VERSION"
