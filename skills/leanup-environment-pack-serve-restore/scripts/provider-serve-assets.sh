#!/usr/bin/env bash
set -euo pipefail

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8765}"
LEANUP_HOME="${LEANUP_HOME:-$HOME/.leanup}"
LEANUP_CACHE_DIR="${LEANUP_CACHE_DIR:-$LEANUP_HOME/cache}"
ROOT="${ROOT:-$LEANUP_CACHE_DIR/serve}"
LOG="${LOG:-$HOME/.leanup/logs/provider-serve.log}"
PIDFILE="${PIDFILE:-$HOME/.leanup/state/locks/leanup-asset-server.pid}"
PYTHON="${PYTHON:-python3}"

mkdir -p "$ROOT" "$(dirname "$LOG")" "$(dirname "$PIDFILE")"

running_pid=""
if [ -f "$PIDFILE" ]; then
  candidate=$(cat "$PIDFILE" 2>/dev/null || true)
  if [ -n "$candidate" ] && kill -0 "$candidate" 2>/dev/null; then
    running_pid="$candidate"
  fi
fi

start_server() {
  cd "$ROOT"
  nohup "$PYTHON" -m http.server "$PORT" --bind "$HOST" >"$LOG" 2>&1 &
  echo $! > "$PIDFILE"
  echo "started pid=$(cat "$PIDFILE") root=$ROOT port=$PORT"
}

if [ -n "$running_pid" ]; then
  running_root=$(readlink "/proc/$running_pid/cwd" 2>/dev/null || true)
  if [ "$running_root" = "$ROOT" ]; then
    echo "already running: pid=$running_pid root=$ROOT port=$PORT"
  else
    echo "restarting: pid=$running_pid old_root=$running_root new_root=$ROOT port=$PORT"
    kill "$running_pid"
    sleep 1
    start_server
  fi
else
  start_server
fi

sleep 1
curl --noproxy '*' -sS "http://127.0.0.1:$PORT/" >/dev/null
echo "local check ok: http://127.0.0.1:$PORT/ root=$ROOT"
