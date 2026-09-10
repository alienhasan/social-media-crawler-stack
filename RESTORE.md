# RESTORE — social-media crawler stack (source-only repository)

This repo is the **setup half** of the live project at
`~/hermesworkspace/social-media` (2.3 GB) and of the local full archive
`~/backups/social-media-full-backup-2026-08-06.tar.gz` (832 MB, made 2026-08-06
on WSL2 / Ubuntu 24.04, Python 3.12.3).

The archive was split into **source** (committed here, ~180 KB) and
**downloadable** (rebuilt by `setup.sh` from PyPI + the Playwright CDN). The
832 MB tarball is *not* in this repo and is not needed to reproduce the setup —
it exists only as a byte-identical local archive.

## Mapping: live / backup path → this repo → restore destination

| Live / backup path | This repo | Restores to |
|---|---|---|
| `social-media/login.py` | `social-media/login.py` | `~/hermesworkspace/social-media/login.py` |
| `social-media/server.py` | `social-media/server.py` | same dir |
| `social-media/cleaner.py` | `social-media/cleaner.py` | same dir |
| `social-media/browser_stealth.py` | `social-media/browser_stealth.py` | same dir |
| `social-media/test_cleaner*.py` (3 files) | same | same dir (hardcoded `/home/openclaw` path rewritten to `$PROJECT_DIR`) |
| `social-media/README.md` (49 KB) | same | same dir |
| `social-media/venv/` (823 MB) | — | **rebuilt**: `python3.12 -m venv` + `pip install -r requirements.txt` |
| `external/ms-playwright/chromium-1234*` | — | **rebuilt**: `playwright install chromium` (playwright 1.62.0 pins 1234) |
| `social-media/fb_state.json` | — | **re-created** by `login.sh facebook` (cookie, excluded on purpose) |
| `social-media/twitter_state.json` | — | **re-created** by `login.sh twitter` (cookie, excluded on purpose) |
| `social-media/ig_state.json` | — | **re-created** by `login.sh instagram` (cookie, excluded on purpose) |
| `social-media/browser_profiles/` (1.5 GB) | — | re-created on first `login.sh` / server run |
| `social-media/fb-login/facebook-browser/` (61 MB) | — | dead scratch profile, not needed |
| `~/.hermes/skills/SocialMediacrawler/SKILL.md` | `SocialMediacrawler-skill/SKILL.md` | `~/.hermes/skills/SocialMediacrawler/SKILL.md` (paths rewritten) |

Deltas versus a byte-identical restore: `.pyc` byte-caches and the browser
binaries are not shipped (regenerable), and installed copies of the skill/tests
get their `/home/openclaw` paths rewritten to the new `$HOME`. The repo keeps the
original text so it stays diff-able.

## Restore on a fresh WSL2 / Ubuntu 24.04

```bash
sudo apt-get update && sudo apt-get install -y git curl python3.12 python3.12-venv

git clone https://github.com/alienhasan/social-media-crawler-stack.git
cd social-media-crawler-stack

bash setup.sh                 # venv + 97 pinned pkgs + chromium 1234
bash login.sh facebook        # visible browser, log in, press Enter
bash login.sh twitter         # (optional, only if you crawl X)
bash login.sh instagram       # (optional, only if you crawl Instagram)
bash run.sh                   # http://localhost:3000
```

Verify:

```bash
curl -s http://localhost:3000/health     # expect "status": "ok"
```

Expect `instagram_session_loaded` / `session_loaded` / `twitter_session_loaded`
to be `false` for any platform whose `login.sh` has not run — that is normal on
a fresh machine.

## Target-machine requirements

- **Ubuntu 24.04 / WSL2**, Python **3.12** (`python3.12 -m venv`; wheels for
  crawl4ai 0.9.2 + playwright 1.62.0 are keyed to 3.12).
- **A GUI for the login step**: WSLg (Windows 11) or an X server. Scraping itself
  is headless, so `run.sh` works without a display.
- `sudo` for the one-time apt packages (`playwright install-deps chromium`
  pulls the chromium shared libs). Use `--skip-system-deps` if you manage them
  yourself.
- ~1.5 GB free disk for venv + chromium builds.

## Exact versions this repo pins

| Package | Version | Note |
|---|---|---|
| Crawl4AI | 0.9.2 | `get_storage_state()` does not exist here — see README §6 Problem #2 |
| playwright | 1.62.0 | drives chromium **1234** (`chromium_headless_shell-1234`, `ffmpeg-1011`) |
| playwright-stealth | 2.0.3 | anti-bot fingerprint |
| Flask | 3.1.3 | HTTP API on port 3000 |
| beautifulsoup4 | 4.15.0 | used by `cleaner.py` |

`requirements.txt` is a full 97-package pin generated from the live venv's
`dist-info` metadata. It is exact *enough* to rebuild; the local venv remains the
reference runtime.

## Security notes

- This repo contains **no cookies and no credentials** — that was deliberate.
  The excluded `*_state.json` and `browser_profiles/` hold live FB/X sessions;
  the local 832 MB tarball *does* contain them, so treat the tarball as a
  credential and the repo as safe.
- The repo is **private** because the code is business-derived.
- After restore, `browser_profiles/` + `*_state.json` are re-created locally and
  are git-ignored, so a later `git status` will stay clean.
