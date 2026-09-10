#!/usr/bin/env bash
# Start the social-media crawler server (Flask + crawl4ai) from the venv.
#
#   bash run.sh            start in the foreground
#   bash run.sh --check    only report whether the server is already up
#
# Env overrides: PROJECT_DIR, VENV, PORT (health-check port only)
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/hermesworkspace/social-media}"
VENV="${VENV:-$PROJECT_DIR/venv}"
PORT="${PORT:-3000}"
URL="http://localhost:${PORT}/health"

health() { curl -s --max-time 5 "$URL" 2>/dev/null || true; }

BODY="$(health)"
if [ "${1:-}" = "--check" ]; then
  case "$BODY" in
    *'"status": "ok"'*|*'"status":"ok"'*) echo "server UP   ($URL -> ok)" ;;
    *) echo "server DOWN ($URL -> ${BODY:-no response})" ;;
  esac
  exit 0
fi
case "$BODY" in
  *'"status": "ok"'*|*'"status":"ok"'*)
    echo "server already running on port $PORT ($URL -> ok)"
    exit 0 ;;
esac

[ -x "$VENV/bin/python" ] || { echo "no venv at $VENV - run: bash setup.sh" >&2; exit 1; }
[ -f "$PROJECT_DIR/server.py" ] || { echo "server.py not found in $PROJECT_DIR - run: bash setup.sh" >&2; exit 1; }

# server.py resolves browser_profiles/ relative to its own file, but keep the
# cwd at the project so state files land next to the code.
cd "$PROJECT_DIR"
echo "starting social-media crawler on http://localhost:$PORT  (Ctrl-C to stop)"
exec "$VENV/bin/python" server.py
