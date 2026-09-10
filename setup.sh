#!/usr/bin/env bash
# =============================================================================
#  social-media crawler stack - source-only bootstrap  (Option A)
#
#  Rebuilds the whole authenticated Facebook / Twitter-X crawling setup on a
#  fresh WSL2 / Ubuntu machine from the sources in this repo. Nothing heavy is
#  committed: pip and playwright download everything for you.
#
#  project code    -> $PROJECT_DIR   (default ~/hermesworkspace/social-media)
#  hermes skill    -> $SKILL_DIR     (default ~/.hermes/skills/SocialMediacrawler)
#  python venv     -> $PROJECT_DIR/venv   (rebuilt from requirements.txt, 97 pkgs)
#  chromium build  -> $PLAYWRIGHT_BROWSERS_PATH  (chromium 1234 via playwright 1.62.0)
#
#  Platforms: facebook (default), twitter/X, instagram.
#
#  NOT included (by design - you said no cookies):
#    fb_state.json, twitter_state.json, ig_state.json, browser_profiles/, fb-login/
#    -> run login.sh once per platform on the new machine to create them.
#
#  Overridable env vars: PROJECT_DIR SKILL_DIR VENV PY_BIN
#                        PLAYWRIGHT_BROWSERS_PATH
#
#  Usage: bash setup.sh [--skip-system-deps] [--skip-browsers] [--force-venv]
#
#  Idempotent - safe to re-run at any time; finished steps are skipped, so a
#  power cut mid-install only costs you the step that was running.
# =============================================================================
set -euo pipefail

usage() {
  sed -n '3,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

REPO_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

PROJECT_DIR="${PROJECT_DIR:-$HOME/hermesworkspace/social-media}"
SKILL_DIR="${SKILL_DIR:-$HOME/.hermes/skills/SocialMediacrawler}"
VENV="${VENV:-$PROJECT_DIR/venv}"
PY_BIN="${PY_BIN:-python3.12}"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"

SKIP_SYSTEM_DEPS=0
SKIP_BROWSERS=0
FORCE_VENV=0

while (($#)); do
  case "$1" in
    --skip-system-deps) SKIP_SYSTEM_DEPS=1 ;;
    --skip-browsers)    SKIP_BROWSERS=1 ;;
    --force-venv)       FORCE_VENV=1 ;;
    -h|--help)          usage; exit 0 ;;
    *) echo "unknown option: $1  (try --help)" >&2; exit 2 ;;
  esac
  shift
done

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m    ok: %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m    WARN: %s\033[0m\n' "$*" >&2; }
die()  { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

# ---------------------------------------------------------------- 1. preflight
say "1/7  preflight"
REQ_FILE="$REPO_DIR/social-media/requirements.txt"
[ -f "$REQ_FILE" ] || die "social-media/requirements.txt not found - run this script from inside the repo clone"
[ -f "$REPO_DIR/social-media/server.py" ] || die "repo checkout looks incomplete (social-media/server.py missing)"

if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  warn "$PY_BIN not found - installing from apt"
  [ "$SKIP_SYSTEM_DEPS" -eq 0 ] || die "$PY_BIN missing and --skip-system-deps given"
  command -v sudo >/dev/null 2>&1 || die "need $PY_BIN and no sudo available to install it"
  sudo apt-get update -qq
  sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
fi
command -v "$PY_BIN" >/dev/null 2>&1 || die "$PY_BIN still missing (Ubuntu 24.04 ships it as python3.12)"
PYVER="$("$PY_BIN" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
[ "$PYVER" = "3.12" ] || die "python 3.12 required (crawl4ai 0.9.2 / playwright 1.62 wheels), found $PYVER"
"$PY_BIN" -c 'import venv' 2>/dev/null || die "$PY_BIN cannot create venvs - apt install python3.12-venv"
ok "$PY_BIN -> $("$PY_BIN" -V 2>&1)"

# ------------------------------------------------------------ 2. project code
say "2/7  project code -> $PROJECT_DIR"
mkdir -p "$PROJECT_DIR"
for f in login.py server.py cleaner.py browser_stealth.py \
         test_cleaner.py test_cleaner_twitter.py test_cleaner_instagram.py \
         README.md requirements.txt; do
  install -m 644 "$REPO_DIR/social-media/$f" "$PROJECT_DIR/$f"
done
chmod 755 "$PROJECT_DIR"/*.py
# the only hardcoded paths in the codebase live in the test scripts
for f in test_cleaner.py test_cleaner_twitter.py test_cleaner_instagram.py; do
  sed -i -e "s|/home/openclaw/hermesworkspace/social-media|$PROJECT_DIR|g" \
         -e "s|/home/openclaw|$HOME|g" "$PROJECT_DIR/$f"
done
ok "8 source files + requirements.txt installed ($PROJECT_DIR)"
if [ -f "$PROJECT_DIR/fb_state.json" ] || [ -f "$PROJECT_DIR/twitter_state.json" ] \
   || [ -f "$PROJECT_DIR/ig_state.json" ]; then
  ok "existing session file(s) left untouched (no re-login needed)"
else
  warn "no session files yet - run: bash login.sh facebook  (and/or: twitter, instagram)"
fi

# ------------------------------------------------------------- 3. hermes skill
say "3/7  hermes skill -> $SKILL_DIR"
mkdir -p "$SKILL_DIR"
install -m 644 "$REPO_DIR/SocialMediacrawler-skill/SKILL.md" "$SKILL_DIR/SKILL.md"
sed -i -e "s|/home/openclaw/hermesworkspace/social-media|$PROJECT_DIR|g" \
       -e "s|/home/openclaw/.hermes/skills/SocialMediacrawler|$SKILL_DIR|g" \
       -e "s|/home/openclaw|$HOME|g" "$SKILL_DIR/SKILL.md"
ok "installed, /home/openclaw paths rewritten to this machine's \$HOME"

# --------------------------------------------------------------------- 4. venv
say "4/7  python venv -> $VENV"
if [ -x "$VENV/bin/python" ] && [ "$FORCE_VENV" -eq 0 ]; then
  ok "existing venv reused ($("$VENV/bin/python" -V 2>&1)) - use --force-venv to rebuild"
else
  if [ "$FORCE_VENV" -eq 1 ]; then
    rm -rf "$VENV"
  fi
  "$PY_BIN" -m venv "$VENV"
  ok "created with $("$VENV/bin/python" -V 2>&1)"
fi

# ------------------------------------------------------------ 5. pip packages
say "5/7  python packages from requirements.txt (97 pinned) - slowest step"
"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel --quiet
"$VENV/bin/python" -m pip install -r "$REQ_FILE"
ok "packages installed"

# ---------------------------------------------------- 6. chromium + apt deps
say "6/7  chromium browser build (playwright 1.62.0 pins chromium 1234)"
if [ "$SKIP_BROWSERS" -eq 1 ]; then
  warn "--skip-browsers given: browser download skipped, scraping will not work until you run it"
else
  if [ "$SKIP_SYSTEM_DEPS" -eq 0 ] && command -v sudo >/dev/null 2>&1; then
    "$VENV/bin/python" -m playwright install-deps chromium \
      || warn "install-deps failed - if chromium cannot start, apt-install its libs manually"
  fi
  "$VENV/bin/python" -m playwright install chromium
  ok "browsers in $PLAYWRIGHT_BROWSERS_PATH"
fi

# -------------------------------------------------------------- 7. verify
say "7/7  verification"
export VENV_PYTHON="$VENV/bin/python"
"$VENV/bin/python" - <<'PY'
import importlib.metadata as md
import json, os, pathlib, sys

bad = False
for pkg in ("Crawl4AI", "Flask", "playwright", "playwright-stealth", "beautifulsoup4"):
    try:
        print(f"    {pkg}=={md.version(pkg)}")
    except Exception as exc:                      # noqa: BLE001
        print(f"    MISSING {pkg} ({exc})")
        bad = True
if bad:
    sys.exit("package check failed")

import bs4, crawl4ai, flask, playwright  # noqa: F401  import smoke test
print("    imports OK")

base = pathlib.Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"])
bjson = pathlib.Path(playwright.__file__).parent / "driver" / "package" / "browsers.json"
revs = {b["name"]: str(b.get("revision")) for b in json.loads(bjson.read_text())["browsers"]}
missing = []
for name in ("chromium", "chromium-headless-shell", "ffmpeg"):
    rev = revs.get(name, "?")
    d = base / f"{name.replace('-', '_')}-{rev}"
    if d.is_dir():
        print(f"    {d.name}: present")
    else:
        print(f"    {d.name}: MISSING")
        missing.append(name)
if missing:
    sys.exit("browser builds missing - run: %s -m playwright install chromium" % os.environ["VENV_PYTHON"])
print("    browser builds match playwright %s" % md.version("playwright"))
PY

cat <<EOF

DONE.

  project ......... $PROJECT_DIR
  hermes skill .... $SKILL_DIR/SKILL.md
  venv ............ $VENV
  browsers ........ $PLAYWRIGHT_BROWSERS_PATH
  server .......... http://localhost:3000  (GET /health, POST /crawl)

Next, once per platform (needs a GUI - WSLg or an X server):

  bash "$REPO_DIR/login.sh" facebook     # -> fb_state.json
  bash "$REPO_DIR/login.sh" twitter      # -> twitter_state.json
  bash "$REPO_DIR/login.sh" instagram    # -> ig_state.json

Then start it:

  bash "$REPO_DIR/run.sh"

Health check:

  curl -s http://localhost:3000/health
EOF
