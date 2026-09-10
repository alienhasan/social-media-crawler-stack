#!/usr/bin/env bash
# Capture a login session for the crawler (Facebook or Twitter/X).
#
#   bash login.sh facebook     # default -> fb_state.json
#   bash login.sh twitter      # -> twitter_state.json
#
# Opens a VISIBLE chromium (needs a GUI: WSLg on Win11, or an X server) with a
# persistent stealth profile. Log in by hand, then press Enter in this terminal
# to save the session and close the browser. Restart the server afterwards.
#
# Env overrides: PROJECT_DIR, VENV
set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-$HOME/hermesworkspace/social-media}"
VENV="${VENV:-$PROJECT_DIR/venv}"
PLATFORM="${1:-facebook}"

[ -x "$VENV/bin/python" ] || { echo "no venv at $VENV - run: bash setup.sh" >&2; exit 1; }

# WSLg exposes X on :0; login.py auto-detects but be explicit when unset.
if [ -z "${DISPLAY:-}" ] && [ -e /tmp/.X11-unix/X0 ]; then
  export DISPLAY=:0
fi
[ -n "${DISPLAY:-}" ] || echo "WARN: DISPLAY unset and no /tmp/.X11-unix/X0 - a headed browser will die." >&2

cd "$PROJECT_DIR"
exec "$VENV/bin/python" login.py --platform "$PLATFORM"
