# social-media-crawler-stack

Source-only bootstrap for the **authenticated Facebook / Twitter-X crawling
server** (crawl4ai 0.9.2 + Playwright 1.62.0 + Flask). Clone this on a fresh
WSL2 / Ubuntu machine, run one script, and you have the same working stack.

The live project is ~2.3 GB (venv 823 MB, browser profiles 1.5 GB, login
cookies). **None of that is committed** — this repo is the ~180 KB of real
source, plus `setup.sh`, which regenerates the heavy parts from the network.

| Committed (un-regenerable) | Not committed (rebuilt / deliberately excluded) |
|---|---|
| `social-media/*.py`, `README.md` | `venv/` (823 MB) → `pip install -r requirements.txt` |
| `social-media/requirements.txt` (97 pinned pkgs) | `browser_profiles/`, `fb-login/` → recreated by `login.sh` |
| `SocialMediacrawler-skill/SKILL.md` | `fb_state.json`, `twitter_state.json` → **cookies, you asked for these out** |
| `setup.sh`, `run.sh`, `login.sh` | — |

## Install

```bash
git clone https://github.com/alienhasan/social-media-crawler-stack.git
cd social-media-crawler-stack
bash setup.sh          # venv + 97 pkgs + chromium 1234  (~5-10 min, ~500 MB)
```

Idempotent: re-run after a power cut and finished steps are skipped. Options:
`--skip-system-deps`, `--skip-browsers`, `--force-venv`.

Override destinations with env vars — `PROJECT_DIR` (default
`~/hermesworkspace/social-media`), `SKILL_DIR` (default
`~/.hermes/skills/SocialMediacrawler`), `VENV`, `PY_BIN`,
`PLAYWRIGHT_BROWSERS_PATH`.

## Log in (once per platform, on the new machine)

Sessions are **not** shipped — FB/X bind them to the device + IP, so a copied
cookie file is both a security problem and the main cause of "unusual login"
flags. Do it fresh:

```bash
bash login.sh facebook     # visible chromium -> log in -> press Enter -> fb_state.json
bash login.sh twitter      # -> twitter_state.json
```

Needs a GUI: **WSLg** (Windows 11) or an X server; `login.sh` sets `DISPLAY=:0`
for WSLg automatically. `login.py` keeps a persistent stealth profile per
platform, so the browser doesn't look like a brand-new device each run.

## Run

```bash
bash run.sh                # http://localhost:3000
bash run.sh --check        # is it up?
curl -s http://localhost:3000/health
```

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url":"https://x.com/search?q=AI&src=typed_query&f=live"}'
```

Rules the server and the skill enforce: **one URL per request**, no concurrent
crawls, never Facebook and Twitter in the same request.

## Verify after install

```bash
curl -s http://localhost:3000/health
# {"status": "ok", "session_loaded": true, "twitter_session_loaded": true, "port": 3000}
```

`sessions_loaded` both `false` until you run `login.sh` — that is expected on a
fresh machine.

## Layout

```
social-media/               login.py server.py cleaner.py browser_stealth.py
                            test_cleaner*.py README.md requirements.txt
SocialMediacrawler-skill/   SKILL.md  (Hermes skill -> ~/.hermes/skills/SocialMediacrawler)
setup.sh run.sh login.sh
RESTORE.md                  path mapping + step-by-step restore
```

`social-media/README.md` is the full 49 KB engineering doc: API reference,
cleaner internals, and 11 documented root-caused bugs — read it before editing.

See `RESTORE.md` for the mapping against the local full backup
(`~/backups/social-media-full-backup-2026-08-06.tar.gz`, 832 MB).
