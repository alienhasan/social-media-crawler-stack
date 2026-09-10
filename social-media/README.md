# Social Media Crawler — Facebook, Twitter/X & Instagram Authenticated Crawling with Crawl4AI

> Project directory: `/home/openclaw/hermesworkspace/social-media`
> Last updated: 2026-09-10

---

## 1. Project Overview

This project lets you **crawl Facebook, Twitter/X and Instagram pages with your
own logged-in accounts** using [Crawl4AI](https://github.com/unclecode/crawl4ai)
(v0.9.2). The main pieces:

| File | Role |
|---|---|
| `login.py` | Opens a **visible (headed) browser**, you log in manually (Facebook, Twitter/X **or** Instagram), and it saves your authenticated session (cookies + localStorage) to `fb_state.json` / `twitter_state.json` / `ig_state.json`. The browser **stays open until you close it**. |
| `server.py` | Flask API server (port **3000**) that loads all session files and crawls any URL — including Facebook, X and Instagram pages — **headlessly with your login cookies**, returning cleaned markdown (noise-filtered by `cleaner.py`) and **structured post JSON for Twitter (X) search pages**. The platform is auto-detected from the URL. |
| `cleaner.py` | **Data cleaner** — strips Facebook, Twitter **and** Instagram chrome / nav / suggestions / sponsored content / reaction counts / notification alerts from the raw markdown before it is returned. |
| `browser_stealth.py` | **Browser-authenticity (stealth) config** shared by `login.py` and `server.py` — real Linux Chrome/151 UA, realistic viewport, `navigator.webdriver` hidden, WebGL kept alive, `window.chrome.runtime` restored, notifications permission normalized, persistent profiles. |
| `test_cleaner.py` | Unit tests for the cleaner (Facebook fixture — 27 assertions). |
| `test_cleaner_twitter.py` | Unit tests for the cleaner (Twitter/X fixture — 31 assertions). |
| `test_cleaner_instagram.py` | Unit tests for the cleaner (Instagram fixture — 25 assertions). |

**Pipeline (Facebook):**

```
python login.py            ──►  manual Facebook login  ──►  fb_state.json (session saved)
                                                                │
python server.py ──►  loads fb_state.json + twitter_state.json ─┤
        │                                                       │
POST /crawl {"url": "https://www.facebook.com/..."} ────────────┘
        │
        └──► headless Chromium + your cookies ──► page HTML/markdown
```

**Pipeline (Twitter/X):**

```
python login.py --platform twitter  ──►  manual X login  ──►  twitter_state.json
                                                                │
python server.py ──►  loads both session files ────────────────┤
        │                                                       │
POST /crawl {"url": "https://x.com/..."} ───────────────────────┘
        │                    (x.com / twitter.com URLs use the Twitter session
        │                     automatically; everything else uses Facebook)
        └──► headless Chromium + your cookies ──► page HTML/markdown
```

**Pipeline (Instagram):**

```
python login.py --platform instagram ──►  manual IG login  ──►  ig_state.json
                                                                │
python server.py ──►  loads all session files ──────────────────┤
        │                                                       │
POST /crawl {"url": "https://www.instagram.com/<user>/"} ───────┘
        │                    (instagram.com URLs use the Instagram session
        │                     automatically; x.com → Twitter, everything else → Facebook)
        └──► headless Chromium + your cookies ──► page HTML/markdown
```

---

## 2. Project Structure

```
/home/openclaw/hermesworkspace/social-media/
├── login.py          # (11 KB) Manual login (Facebook default, Twitter/X + Instagram via --platform) → fb_state.json / twitter_state.json / ig_state.json
├── server.py         # (15 KB) Flask API: authenticated crawling + platform auto-detection + search extraction + cleaner wiring
├── cleaner.py        # (23 KB) Data cleaner: 3-tier line-based FB + Twitter/X + Instagram noise filter
├── test_cleaner.py   # (4.9 KB) Unit tests for cleaner.py Facebook path (27 assertions)
├── test_cleaner_twitter.py  # (4.9 KB) Unit tests for cleaner.py Twitter/X path (31 assertions)
├── test_cleaner_instagram.py# (4.7 KB) Unit tests for cleaner.py Instagram path (25 assertions)
├── fb_state.json     # (2.3 KB) Saved Facebook session (cookies + origins) — YOUR login
├── twitter_state.json# (created by `login.py --platform twitter`) Saved X session
├── ig_state.json     # (created by `login.py --platform instagram`) Saved Instagram session
├── browser_stealth.py# (6.5 KB) Shared stealth config: real UA, viewport, init script, persistent profiles
├── browser_profiles/ # Persistent browser profiles (real history/cache) — created on first run
│   ├── facebook/     #   login.py (Facebook) profile
│   ├── twitter/      #   login.py --platform twitter profile
│   ├── instagram/    #   login.py --platform instagram profile
│   └── server/       #   server.py headless crawl profile
├── venv/             # Python 3.12.3 virtual environment
│   └── lib/python3.12/site-packages/
│       ├── crawl4ai 0.9.2
│       ├── flask 3.1.3
│       ├── playwright 1.62.0
│       ├── playwright-stealth (stealth evasions for crawl pages)
│       └── pydantic 2.13.4
└── __pycache__/      # Python bytecode cache (auto-generated)
```

**Environment:** WSL2 (Windows Subsystem for Linux) with **WSLg** (GUI support),
Ubuntu 24.04, Python 3.12.3, Chromium via Playwright
(`~/.cache/ms-playwright/chromium-1234`).

---

## 3. How It Works

### 3.1 `login.py` — capture the session

1. **Auto-detects a display** for the headed browser (see Problem #1 below).
2. Launches a visible Chromium via Crawl4AI's browser manager
   (`headless=False`).
3. Opens the platform's login page and **waits for you to log in** — no time
   limit, the browser never closes by itself.
4. Polls cookies every 2 s for the platform's login cookie; the moment it
   appears, the session is saved automatically.
5. Pressing **Enter** in the terminal also saves the current session.
6. After a successful login is detected, the browser **stays open** until you
   press **Enter** (or **Ctrl+C**) to close it.
7. The browser uses a **persistent profile** (`browser_profiles/<platform>`),
   so it keeps real history/cache/localStorage between runs instead of
   looking like a brand-new device every time (see section 3.3).

Platforms (`--platform`, default `facebook`):

| Platform | `--platform` | Login page | Login cookie | Output |
|---|---|---|---|---|
| Facebook | *(default)* | `https://www.facebook.com/` | `c_user` | `fb_state.json` |
| Twitter / X | `twitter` | `https://x.com/` | `auth_token` | `twitter_state.json` |

Output: a standard Playwright storage-state file:

```json
{
  "cookies": [ { "name": "c_user", "value": "6159094...", "domain": ".facebook.com", ... },
               { "name": "xs", ... }, { "name": "sb", ... }, { "name": "datr", ... },
               { "name": "fr", ... }, { "name": "wd", ... } ],
  "origins": [ { "origin": "https://www.facebook.com", "localStorage": [...] } ]
}
```

### 3.2 `server.py` — crawl with the session

- Loads `fb_state.json` **once at startup** into `STORAGE_STATE`, and
  `twitter_state.json` into `TWITTER_STORAGE_STATE`.
- Each `/crawl` request detects the platform from the URL
  (`x.com` / `twitter.com` → Twitter, everything else → Facebook) and runs a
  headless `AsyncWebCrawler` with a **persistent profile**
  (`browser_profiles/server`) and the stealth config from
  `browser_stealth.py` (section 3.3). The saved session is injected into the
  browser context **manually** (`context.add_cookies()` + per-origin
  `localStorage` init scripts) — `BrowserConfig(storage_state=...)` crashes
  Crawl4AI 0.9.2's persistent launch, so it isn't used. You can override the
  platform detection with the optional `"platform"` body param.
- For normal pages (single tweets, profiles, Facebook) the raw Crawl4AI
  markdown is passed through `cleaner.clean_markdown(..., platform=...)`
  (noise filter — see section 5) **before** it is returned.
- **Twitter (X) search URLs** (`x.com/search?q=...`) skip the markdown path
  and return **structured post JSON** (author, text, url, timestamp, media,
  replies, reposts, likes) — see section 3.4.
- Returns (non-search): `success`, `url`, `platform`, `html_length`, the
  **cleaned** `markdown` (post content only), `cleaning_stats` (how much
  noise was removed), and a `screenshot` (if produced).
- **Scrolling is enabled** (`scan_full_page=True`, `max_scroll_steps=15` by
  default) because Facebook and X load posts **lazily as you scroll** —
  without it the DOM contains only the page shell and a few posts (see
  Problem #8). Search pages use their own in-page scroll loop instead
  (section 3.4).

> **Important:** sessions are read at startup. After re-logging in, restart
> `server.py` so it picks up the fresh cookies.

### 3.3 Browser authenticity / stealth (`browser_stealth.py`)

Playwright-controlled Chromium is detectable as automated, and Twitter/X
reacts by restricting the account. Both `login.py` and `server.py` now share
one stealth configuration (`browser_stealth.py`) so the login browser and the
crawler have the **same, consistent fingerprint**:

| Signal | Before | After |
|---|---|---|
| `navigator.userAgent` | `Chrome/116` on macOS (stale, mismatched with engine + client hints) | real `Chrome/151.0.0.0` Linux — matches the installed Chromium binary and `Sec-CH-UA` |
| `navigator.webdriver` | flagged | hidden (`undefined`) |
| WebGL | **dead** (`null` renderer — Crawl4AI's dedicated launch hardcodes `--disable-gpu`) | **alive** via the persistent-context launch (SwiftShader — truthful for WSLg, no vendor spoof) |
| `window.chrome.runtime` | missing | present |
| viewport / window | Playwright default `1080x600` | realistic `1366x768` + matching `--window-size` |
| notifications permission | `denied` (headless) | `default` (like a real browser) |
| `navigator.platform` | `Win32` (playwright-stealth's stock spoof) | `Linux x86_64` (consistent with UA + client hints) |
| browser profile | brand-new ephemeral profile every launch (= "new device") | **persistent profile** per platform (`browser_profiles/facebook`, `browser_profiles/twitter`) and for crawls (`browser_profiles/server`) — real history/cache/localStorage accumulate over time |

Implementation notes:
- `enable_stealth=True` + `use_persistent_context=True` are used because
  Crawl4AI's persistent launch path respects `enable_stealth` (WebGL stays
  alive) while the dedicated path hardcodes `--disable-gpu` (WebGL dies).
- playwright-stealth (`venv` dependency) runs on crawl pages; its stock
  `navigator_platform_override="Win32"` is patched to `Linux x86_64` and its
  webgl/UA evasions are disabled (the context UA and SwiftShader are already
  correct), so nothing contradicts the Linux fingerprint.
- A defensive init script is injected into **every** context (works even
  without playwright-stealth): hides `webdriver`, restores
  `chrome.runtime`, keeps languages/plugins sane, normalizes notifications.
- **Crawl4AI 0.9.2 bug worked around:** `BrowserConfig(storage_state=...)`
  crashes the persistent launch (`launch_persistent_context()` doesn't accept
  `storage_state`). `server.py` therefore injects the saved session manually
  (`context.add_cookies()` + per-origin `localStorage` init scripts) into a
  pre-created session context before `arun()`.

### 3.4 Twitter (X) search results — structured extraction

`POST /crawl` on an X search URL (`x.com/search?q=...&src=typed_query[&f=live]`)
returns **structured JSON per post** instead of cleaned markdown:

```json
{
  "success": true,
  "url": "https://x.com/search?q=...",
  "platform": "twitter",
  "search": true,
  "query": "automation services",
  "result_count": 80,
  "results": [
    {
      "author": "@GoogleDeepMind",
      "text": "…post text…",
      "url": "https://x.com/GoogleDeepMind/status/123456789",
      "timestamp": "2026-07-30T02:26:00.000Z",
      "media": ["https://pbs.twimg.com/media/…"],
      "replies": 12,
      "reposts": 34,
      "likes": 56
    }
  ]
}
```

How it works:
- Search pages are auto-detected (`x.com/search`/`twitter.com/search` + `q=`).
- They use `wait_until="domcontentloaded"` (X's `load` event never fires) and
  a 120 s page timeout.
- **X virtualizes the timeline**: only ~3-9 articles stay in the DOM near the
  viewport; scrolled-past posts are unmounted. The extraction script
  therefore scrolls **one viewport at a time and extracts on every step**,
  merging into a URL-deduped map — capturing every post as it passes through.
  Promoted/ads posts are skipped; `blob:`/`data:` media URLs are filtered out.
- Volume is controlled by `max_scroll_steps` (default **60** for search):
  ~0.7-0.9 s per step. Measured: 60 steps → 80 posts (~35 s), 120 steps →
  290 posts (~90 s) on the Live tab. Raise it (e.g. 150-300) for deep
  collection, lower it for speed. Scrolling stops early automatically when
  the timeline ends ("You're all caught up").
- Single-tweet and profile URLs keep the **existing cleaned-markdown output
  exactly as before** — only `x.com/search?…` URLs take this path.

### 3.5 Instagram (`instagram.com`)

Instagram profiles, posts and Reels are crawled through the **same markdown
path as Facebook** — no custom extractor — with an Instagram-tuned crawler
config and its own cleaner pattern set (`platform="instagram"`).

| Aspect | Value | Why |
|---|---|---|
| Session | `ig_state.json` (login cookie `sessionid`) | IG sets `sessionid` only after a real login |
| Profile dir | `browser_profiles/instagram/` (login), `browser_profiles/server/` (crawl) | persistent, one browser instance per profile |
| `wait_until` | `domcontentloaded` | IG is a React SPA; its `load` event can stay pending indefinitely (same class of problem as X search pages) |
| `page_timeout` | 90 s | slower than FB's 60 s |
| `delay_before_return_html` | 4.0 s | feed/profile grid renders after hydration |
| `scan_full_page` / `scroll_delay` | on / 0.5 s | the profile grid + feed lazy-load |
| `max_scroll_steps` (default) | **20** | override per request like the other platforms |
| Cleaner | `platform="instagram"` | IG chrome differs from FB/X: nav rail (`Home/Search/Explore/Reels/Messages/Notifications/Threads`), Follow/Message buttons, follower stats, "Suggested for you", "More posts from …", `Liked by … and N others`, the `Log in to like or comment` wall, and IG's **joined-together footer language list** (dropped when 4+ language names appear on one line) |

Bengali IG UI strings (`ফলো করুন`, `শেয়ার`, `সেভ`, `আরও দেখুন`, `নোটিফিকেশন`, …)
are filtered by the same pattern set, so both English and Bengali accounts
produce clean output.

**What survives cleaning** (the lead-gen signal): the username line, the profile
bio, the location line, post captions (English + Bengali), and real comments —
including comments that contain a phone number or a question, which is exactly
what you want to pitch automation services against.

**Known limitation:** a *suggested-account* handle line (e.g. a row under
"Suggested for you") can survive, because it is indistinguishable from a real
username line without page context. Same class of residue as FB's
people-you-may-know cards. Everything else in the IG chrome is filtered.

---

## 4. API Reference

### `GET /health`

```bash
curl http://localhost:3000/health
```

```json
{ "status": "ok", "session_loaded": true, "twitter_session_loaded": false,
  "instagram_session_loaded": false, "port": 3000 }
```

(`session_loaded` = Facebook session present, `twitter_session_loaded` =
Twitter/X session present, `instagram_session_loaded` = Instagram session
present. A `false` just means that platform's `login.py` run has not happened
yet — the server still works for the platforms that have sessions.)

### `POST /crawl`

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.facebook.com/some-page"}'
```

Twitter/X works the same way — just pass an `x.com` / `twitter.com` URL (the
server uses the Twitter session automatically):

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://x.com/some-user"}'
```

Instagram works the same way too — pass an `instagram.com` URL and the
Instagram session (see section 3.5):

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/some-user/"}'
```

Optional body fields: `max_scroll_steps` (int), `clean` (bool, default `true`),
`exclude_patterns` (list of extra regexes), `platform`
(`"facebook"` / `"twitter"` / `"instagram"` — normally auto-detected from the
URL).

**Twitter (X) search pages** (`x.com/search?q=…&src=typed_query[&f=live]`)
return structured post objects (author, text, url, timestamp, media,
replies, reposts, likes) — see section 3.4:

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://x.com/search?q=automation%20services&src=typed_query&f=live", "max_scroll_steps": 120}'
```

**Optional body params:**

| Param | Default | Meaning |
|---|---|---|
| `url` | — | Page to crawl (**required**) |
| `max_scroll_steps` | `15` (X search: `60`) | Scroll steps to load lazily-rendered posts. More = more posts, slower crawl (each step ≈ 0.4 s for normal pages, ≈ 0.7-0.9 s for X search). `40` ≈ a long feed; `0` disables scrolling. For X search raise it (e.g. `150-300`) to collect deep result sets. |
| `clean` | `true` | Run the noise filter (`cleaner.py`) on the markdown. Pass `false` (or `"false"`/`"0"`/`"no"`) to get the **raw** Crawl4AI markdown instead. |
| `exclude_patterns` | — | Optional list of **regex patterns** (strings) to drop lines containing them — e.g. `["বিক্রয়", "job", "news"]` to exclude promos/job ads/news. Applied to lines of **any** length, in addition to the built-in filters. |
| `platform` | auto | Optional override: `"facebook"` or `"twitter"`. Omit to auto-detect from the URL (`x.com`/`twitter.com` → twitter, else facebook). |

**Note:** `clean` and `exclude_patterns` apply to the markdown path only —
X search URLs always return structured JSON (section 3.4) and ignore them.

**Response (success, `clean: true`):**

```json
{
  "success": true,
  "url": "https://www.facebook.com/...",
  "platform": "facebook",
  "html_length": 4054721,
  "markdown": "[cleaned markdown — only real post text/author lines, all FB chrome removed]",
  "cleaning_stats": {
    "original_lines": 306,
    "removed_lines": 298,
    "kept_lines": 8,
    "original_chars": 58572,
    "cleaned_chars": 297,
    "removed_chars": 58275,
    "removed_pct": 99
  },
  "screenshot": null
}
```

(`"platform"` is `"twitter"` for `x.com`/`twitter.com` crawls.)

`cleaning_stats` is `null` when `clean: false` (raw markdown returned).

**Response (failure):** `{ "success": false, "url": "...", "platform": "...", "error": "..." }`

If the platform's session file is missing (e.g. Twitter before running
`login.py --platform twitter`), the response is `{ "error": "..." }` telling
you to run the right login command.

---

## 5. Output Cleaning — Data Cleaner (`cleaner.py`)

Crawl4AI's raw markdown of a Facebook or Twitter/X page is ~90 % chrome:
navigation menus, suggestion rails, reaction icons (giant SVG data-URIs),
notification alerts, like/comment counts, cookie prompts and URL soup.
`cleaner.py` removes this noise so the API returns **only meaningful post
content**.

**Platforms:** `clean_markdown(..., platform="facebook")` (default — unchanged
behavior) and `platform="twitter"` use **separate pattern sets** — Facebook
and X chrome are different. The server passes the platform it detected from
the URL; standalone callers can pass it explicitly. The shared always-drop
rules (pure URLs, separators, pure numbers, emoji-only, obfuscated
zero-width junk) and the `exclude_patterns` / dedupe / `min_block_chars`
logic apply to both.

### 5.1 How it works

Cleaning is **line-based** (not block-based) because Crawl4AI's FB markdown is
a wall of lines with almost no blank-line separators — block splitting would
leave one giant block and filter nothing. The pipeline per line:

1. **Preprocessing** (`_clean_line`):
   - Removes markdown **image links** entirely (`![](...)`), including the
     huge `data:image/svg+xml,...` reaction icons. The regex tolerates
     **escaped parentheses** (`\(` `\)`) inside SVG URLs — a plain
     `[^)]*` pattern stops mid-URI and leaks thousands of junk characters.
   - Rewrites `[text](url)` → just `text`, so menu items like
     `[Friends](https://www.facebook.com/friends/)` become plain `Friends`
     and URL clutter disappears.
   - Drops lines that are still pure encoded junk (≥ 5 percent-encoded
     sequences — broken SVG fragments), contain `data:image/` or
     `fbcdn.net/rsrc.php`, or become empty after the rewrites.
   - Strips markdown markers (`#` headings, `*` bullets, `>` quotes,
     `1.` lists), trailing separators (`· • |`) and collapses whitespace.
2. **Noise classification** (`_is_noise_line`) — three tiers:
   - **Tier 1 — Strong labels** (line *starts* with these → always dropped):
     `Sponsored`, `স্পনসরড`, `Suggested for you`, `People you may know`,
     `You might like`, `পরামর্শ`, `Recommended`, `Log in to Facebook`,
     `Create new account`, …
   - **Tier 2 — All-line patterns** (matched *anywhere*, any length — FB
     chrome that almost never appears inside a real post): `photos from`,
     `m.me`, `mobile uploads`, `Verified account`, `Learn More`,
     `We noticed a new login…`, `Your full control … was removed`,
     `You can help grow…`, `Create an ad today…`, `What's on your mind…`,
     `Create a post`, `Feed posts`, `Facebook menu`, `Your shortcuts`,
     `Find friends`, `See previous notifications`, `Unread`, `See
     translation` / `অনুবাদ দেখুন`, …
   - **Tier 3 — Short-line patterns** (only lines ≤ 160 chars, so real post
     text is never caught): navigation items (`Home`, `Watch`,
     `Marketplace`, `Groups`, `Friends`, …), action bars (`Like`,
     `Comment`, `Share`), reaction counts (`1.2K`, `270`), timestamps
     (`2 h`, `16 hours ago`, `5w`), `See more`/`See all`/`View all`,
     cookie/privacy/terms lines, Bengali chrome (`মন্তব্য লিখুন`, `আরও
     দেখুন`, `লাইক`, `কমেন্ট`, `শেয়ার`, `ঘণ্টা আগে`), and more.
   - **Always dropped:** pure URLs, separators (`---`, `• • •`), pure
     numbers, emoji-only lines, and lines with > 8 combining/zero-width
     characters (Facebook **obfuscates** image-post placeholder text with
     `U+034F`-style characters, e.g. `r͏S͏e͏t͏s͏o͏p͏d͏n͏o͏f͏…` — an
     anti-scrape measure).
   - **User `exclude_patterns`** (passed via the API) are applied to lines
     of any length, on top of the built-in tiers.
3. **Post-filter:** lines shorter than `min_block_chars` (default 10) are
   dropped, and exact duplicates are removed (case-insensitive, order
   preserved).

Long lines (> 160 chars) are treated as real post text and only Tier 1/2
patterns (strong labels, all-line patterns, user exclusions) apply to them —
a generic pattern like `see more` will never delete a long post.

### 5.2 What it removes (real examples)

| Noise | Example | Removed by |
|---|---|---|
| Navigation / sidebar | `Home`, `Watch`, `Marketplace`, `Groups` | Tier 3 |
| Menu links | `[Friends](url)`, `[Find friends](url)`, `[See all](url)` | Preprocess → Tier 3 / Tier 2 |
| Suggestion rails | `Suggested for you`, `People you may know` | Tier 1 |
| Sponsored / ads | `Sponsored`, `Your business is ready. Create an ad today…` | Tier 1 / Tier 2 |
| Login / cookie prompts | `Log in to Facebook`, `Allow cookies`, `Privacy`, `Terms` | Tier 1 / Tier 3 |
| Reaction icons | `![](data:image/svg+xml,…)` (multi-KB blobs) | Preprocess |
| Image-post placeholders | `m.me Photos from X's post …` (obfuscated string) | Tier 2 + obfuscation check |
| Notification alerts | `We noticed a new login…`, `Your full control … was removed` | Tier 2 |
| Post action bars | `Like`, `Comment`, `Share`, `Write a comment…` | Tier 3 |
| Counts | `1.2K`, `270`, `13`, `42` | Pure-number rule |
| Timestamps | `2 h`, `16 hours ago`, `5w`, `গতকাল` | Tier 3 |
| Duplicates | repeated sidebar/post lines | Dedupe |

### 5.3 Cleaning statistics

Every cleaned response includes `cleaning_stats`:

| Field | Meaning |
|---|---|
| `original_lines` | input lines |
| `removed_lines` | lines dropped by the filter |
| `kept_lines` | lines returned |
| `original_chars` | input size (chars) |
| `cleaned_chars` | output size (chars) |
| `removed_chars` | bytes of noise removed |
| `removed_pct` | `round(removed_chars / original_chars * 100)` |

**Measured on a live crawl of the logged-in FB feed (2 scroll steps):**
306 lines / 58,572 chars in → **8 lines / 297 chars out (99 % noise
removed)** — what remains is exactly the real posts: author names (bold)
and post text.

### 5.4 Using it

- **Via the API (default):** `POST /crawl` cleans automatically (with the
  platform detected from the URL). Add `"clean": false` to get the raw
  markdown, or pass `"exclude_patterns"` to add your own filters.
- **Standalone** (e.g. in a script or n8n workflow):

  ```python
  from cleaner import clean_markdown
  res = clean_markdown(raw_markdown)                    # Facebook (default)
  res = clean_markdown(raw_markdown, platform="twitter")  # Twitter/X
  clean_text = res["cleaned"]   # stats: res["removed_pct"], res["kept_lines"], ...
  ```

- **Tests:** `python3 test_cleaner.py` — 27 assertions (Facebook fixture);
  `python3 test_cleaner_twitter.py` — 31 assertions (Twitter/X fixture;
  both pass).

### 5.5 Twitter/X cleaning (what the Twitter pattern set removes)

| Noise | Example | Removed by |
|---|---|---|
| Nav / tabs | `For you`, `Following`, `Explore`, `Notifications`, `Messages`, `Chat`, `Creator Studio`, `Accessibility`, `PostsPosts`, `HomeExploreNotifications…` (concatenated) | Tier 3 |
| Action bar | `Reply`, `Repost`, `Like`, `View`, `Bookmark`, `Share` | Tier 3 |
| Reply chrome | `Replying to @handle` | Tier 1 |
| Counts / stats | `1.2K`, `2,345 replies`, `1,381 Following 241.1M Followers …`, `1,234` | Tier 3 / pure-number |
| Timestamps | `2h`, `· 5h`, `Jan 5, 2026`, `12:34 AM` | Tier 3 |
| Promoted / ads | `Promoted`, `Ad` | Tier 1 / Tier 3 |
| Trends / sidebar | `Trending now`, `What's happening`, `Who to follow`, `#Automation` | Tier 1 / Tier 3 / hashtag rule |
| Login wall | `New to X?`, `Sign up now`, `Already have an account? Log in`, `Sign in to X`, `Log inSign up` | Tier 1 / Tier 3 |
| Profile meta | `Joined March 2021`, `Following`, `Followers` | Tier 2 / Tier 3 |
| Footer / page title | `Terms·Privacy·Cookies·…© 2026 X Corp.`, `Scan to get the app`, `Elon Musk (@elonmusk) / X` | Tier 3 |
| Status-page chrome | `Conversation`, `View quotes`, `Post your reply`, `Everyone can reply`, `Relevant people`, `To view keyboard shortcuts…`, `See new posts`, `Politics · Trending`, `Click to Unfollow…` | Tier 3 |
| Bengali X UI | `উত্তর দিন`, `রিপোস্ট`, `লাইক`, `বুকমার্ক`, `আরও দেখুন`, `ট্রেন্ডিং` | Tier 3 |

Author attribution is **kept**: lines like `Elon Musk @elonmusk · 2h`
survive, so you know who wrote each kept tweet. **Measured on a live crawl of
`x.com/elonmusk` (4 scroll steps, unauthenticated stub session):** 9,633 chars
in → **1,148 chars out (88 % noise removed)** — remaining lines are the real
tweets (SpaceX broadcast post, replies, author lines). **Measured on the
authenticated single-tweet crawl** (`x.com/GeminiApp/status/…`): 6,985 chars
in → **1,259 chars out (82 % removed)** — the tweet, its link and all replies
kept; status-page chrome removed.

### 5.6 Instagram cleaning (what the Instagram pattern set removes)

`clean_markdown(..., platform="instagram")` uses a third pattern set (IG chrome
is neither FB's nor X's):

| Noise | Example | Removed by |
|---|---|---|
| Nav rail / tabs | `Home`, `Search`, `Explore`, `Reels`, `Messages`, `Notifications`, `Create`, `Threads`, `More`, `Profile`, `HomeSearchExploreReels…` (concatenated), `PostsReelsTagged` | Tier 3 |
| Action bar | `Like`, `Comment`, `Share`, `Save`, `Send`, `Embed`, `Report`, `Copy link`, `Add to story` | Tier 3 |
| Follow chrome | `Follow`, `Following`, `Follow back`, `Message`, `Verified`, `Requested` | Tier 3 |
| Counts / stats | `1,234 posts`, `12.4K followers`, `890 following`, `45 likes` | Tier 3 |
| Timestamps | `2 hours ago`, `3d`, `January 5`, `January 5, 2026` | Tier 3 |
| Likes line | `Liked by karim_uddin and 45 others`, `Followed by rahim_ahmed and 12 others` | Tier 3 |
| Login wall / composer | `Log in to like or comment`, `Add a comment`, `Create an account or log in`, `Log in` (any leading), `Post` | Tier 1 / Tier 3 |
| Suggestions | `Suggested for you`, `Discover people`, `Accounts you follow` | Tier 1 |
| Profile blocks | `More posts from <user>`, `View more on Instagram`, `See photos and videos from <user>`, `Edit profile`, `Share profile`, `Switch accounts` | Tier 1 / Tier 2 |
| Footer links | `About Blog Jobs Help API Privacy Terms Locations Instagram Lite Threads`, `Contact Uploading & Non-Users`, `Meta Verified` | Tier 2 / Tier 3 |
| Footer copyright | `© 2026 Instagram from Meta` | Tier 2 |
| Footer **language blob** | `AfrikaansČeštinaDanskDeutschΕλληνικάEnglish…বাংলা` all on ONE line | `IG_LANG_HITS` rule (≥ 4 language names on a line) |
| Bengali IG UI | `ফলো করুন`, `শেয়ার`, `সেভ`, `আরও দেখুন`, `নোটিফিকেশন`, `সেভ করা` | Tier 3 |

**Kept:** username, bio/caption text, location line, real comments.
**Measured on the cleaner unit-test fixture** (`test_cleaner_instagram.py`,
44 synthetic lines mirroring a logged-in business profile): 1,039 chars in →
**284 chars out (73 % noise removed)**, 39 of 44 lines dropped, 5 kept
(username, Bengali bio, location, one suggested-handle line, one real Bengali
comment asking for a price). The suggested-handle line is a known survivor —
see section 3.5.

---

## 6. Problems Solved (Root-Cause Analysis)

### Problem #1 — Browser opened then closed after a few seconds ❌→✅ *(the main bug)*

**Symptom:** running `login.py` launched a browser window that vanished within
~2 seconds.

**Root cause:** the script requested a **headed (GUI) browser**
(`headless=False`) but **`DISPLAY` was not set**. On WSL, WSLg runs an X server
at `/tmp/.X11-unix/X0` (display `:0`), but the environment variable is not
exported in non-interactive / agent shells. Chromium started, failed with:

```
playwright._impl._errors.TargetClosedError: BrowserType.launch: Target page,
context or browser has been closed
Looks like you launched a headed browser without having a XServer running.
[pid=875][err] Missing X server or $DISPLAY
[pid=875][err] The platform failed to initialize. Exiting.
```

…and the script's `finally: await crawler.close()` finished the job.

**Fix:** `ensure_display()` in `login.py` scans `/tmp/.X11-unix/X*` and sets
`DISPLAY=:N` (usually `:0`) **before** Chromium launches.

### Problem #2 — `crawler.get_storage_state()` doesn't exist in Crawl4AI 0.9.2 ❌→✅

**Symptom:** the original script would have crashed with `AttributeError` right
after login (verified in source: the method was removed in the 0.9 rewrite).

**Fix:** use the browser manager's live-page API and plain Playwright's storage
state — both verified working in 0.9.2:

```python
page, context = await crawler.crawler_strategy.browser_manager.get_page(
    CrawlerRunConfig(session_id="fb-login")
)
state = await context.storage_state()   # → {"cookies": [...], "origins": [...]}
```

(`crawler.crawler_strategy.export_storage_state()` is also broken in 0.9.2 —
`AttributeError: ... no attribute 'default_context'`.)

### Problem #3 — `arun()` is a crawl cycle, not an interactive session ❌→✅

**Symptom/design flaw:** the original script used
`await crawler.arun(url="https://www.facebook.com/")` and then `input()`. But
`arun()` navigates, extracts, and **tears the page/context down** afterwards —
you can never actually log in through it, and any failure path skipped the
`input()` wait and closed the browser immediately.

**Fix:** `login.py` now uses `get_page()` to obtain a **live** page/context,
keeps it open, and polls for the `c_user` cookie instead of relying on `arun()`.

### Problem #4 — Ctrl+C hung forever ❌→✅

**Symptom:** pressing Ctrl+C (SIGINT) left the process and browser alive
indefinitely; shutdown never completed.

**Root cause:** the default KeyboardInterrupt path cancels the asyncio task
**mid-Playwright-call**, wedging the browser protocol, so `crawler.close()`
never finished.

**Fix:** install a **signal handler** (`loop.add_signal_handler(SIGINT, ...)`)
that only sets a flag; all wait loops check the flag; `crawler.close()` then
runs in a normal, never-cancelled task. Second Ctrl+C force-quits.

### Problem #5 — Flask was missing ❌→✅

**Symptom:** `server.py` crashed at import:

```
ModuleNotFoundError: No module named 'flask'
```

**Fix:** `venv/bin/python -m pip install flask` (now flask 3.1.3).

### Problem #6 — Broken mixed-language print ❌→✅

`server.py` line 12 contained corrupted auto-generated text (`✅ সেশন লোড成功`
— Bengali mixed with a Chinese character). Fixed to proper Bengali:
`✅ সেশন লোড হয়েছে (fb_state.json)`.

### Problem #7 — No real-time output when redirected ❌→✅

**Symptom:** with stdout redirected to a file, progress messages were
block-buffered and invisible until exit.

**Fix:** `sys.stdout.reconfigure(line_buffering=True)` at the top of `login.py`.

### Bonus — stdin reader must be a daemon thread

`run_in_executor`/`asyncio.to_thread` blocked interpreter shutdown (asyncio
waits for executor threads). The stdin reader is now a **daemon thread**
feeding a queue; the async loop polls the queue — no executor involvement.

### Problem #8 — `/crawl` returned no posts, only the navbar ❌→✅

**Symptom:** `POST /crawl` on `https://www.facebook.com/zuck` returned
`success: true` with 3.1 MB of HTML, but the markdown showed only page chrome
("Find friends", notification count, profile header) — no post text, no post
links.

**Root cause (two bugs):**

1. **Truncation:** `server.py` returned `result.markdown[:1000]`. The full
   markdown was 21 KB+ and the first 1000 chars are all chrome (nav, cover
   photo, profile intro). Real posts only appear near the end of the
   markdown, in the `## Posts` section.
2. **Lazy loading:** Facebook renders the page shell first and loads posts
   **as you scroll**. Crawl4AI's `scan_full_page` (auto-scroll) defaults to
   `False`, so the DOM was extracted with only ~3 post containers.

**Fix (verified live):**

```python
run_config = CrawlerRunConfig(
    verbose=False,
    wait_until="load",            # wait for the page shell
    delay_before_return_html=3.0, # give posts time to render
    scan_full_page=True,          # scroll to trigger lazy loading
    scroll_delay=0.4,
    max_scroll_steps=15,
)
```

plus returning the **full** `result.markdown` instead of `[:1000]`. After the
fix: 4 MB HTML, 76 KB markdown, real post bodies (e.g. "Benny's first 4th.
Welcome to the fam 🇺🇸" with photo link and "Shared with Public").

**Pitfall:** do **not** use `wait_for="div[role='article']"` on Facebook — it
timed out and failed the whole crawl. Use `delay_before_return_html` instead.
Also note Facebook obfuscates some link text with zero-width characters (e.g.
`e͏p͏o͏t͏S͏s͏o͏r͏d͏n...`) as an anti-scrape measure — strip `\u200b`-style
chars when parsing post text.

### Problem #9 — `/crawl` output was full of noise ❌→✅

**Symptom:** `POST /crawl` returned tens of thousands of characters of
Facebook chrome — nav menus, `Suggested for you` rails, reaction-icon SVG
blobs (multi-KB each), notification alerts, like/comment counts, cookie
prompts — with the actual post text buried in the middle.

**Root cause:** the API returned Crawl4AI's **raw** markdown verbatim. Raw FB
markdown is ~90 % page chrome; it is also a wall of lines with almost no
blank-line separators, so block-based text cleaning leaves a single giant
block and filters nothing.

**Fix:** new `cleaner.py` module — a **line-based, 3-tier** noise filter
(`STRONG_LABELS` → `ALL_LINE_PATTERNS` → `NOISE_PATTERNS` for short lines),
with preprocessing that strips image/data-URI links (regex tolerant of
escaped parens inside SVG URLs), rewrites `[text](url)` → `text`, detects
percent-encoded junk and obfuscated zero-width strings, dedupes, and reports
`cleaning_stats`. `server.py` runs it on every crawl by default (see
section 5). Verified live: **58,572 chars → 297 chars (99 % removed)**.

### Problem #10 — Twitter flagged the login browser as "unusual" ❌→✅

**Symptom:** logging into Twitter/X via `login.py` triggered a temporary
login restriction ("unusual activity").

**Root cause (measured fingerprint):** the Playwright-controlled Chromium
looked automated —
- WebGL was **dead**: Crawl4AI's dedicated launch path hardcodes
  `--disable-gpu --disable-software-rasterizer`, so `WEBGL_debug_renderer_info`
  returned `null` (a strong headless/automation signal);
- the User-Agent said `Chrome/116` on macOS while the real engine was
  Chromium 151 on Linux (UA string ≠ Sec-CH-UA client hints ≠ engine);
- `window.chrome.runtime` was missing; the viewport was Playwright's default
  `1080x600`; headless notifications permission was `denied`;
- every launch used a **fresh ephemeral profile** (= "brand-new device").

**Fix:** new `browser_stealth.py` (section 3.3) — real Linux Chrome/151 UA,
WebGL kept alive via `use_persistent_context=True` + `enable_stealth=True`
(the persistent launch path respects stealth; the dedicated path doesn't),
`navigator.webdriver` hidden, `chrome.runtime` restored, notifications
normalized, realistic 1366x768 viewport, playwright-stealth defaults patched
to stay Linux-consistent, and **persistent per-platform profiles**
(`browser_profiles/`). Verified: the headed login browser, the headless
crawler and real `arun()` pages all expose an identical, consistent
fingerprint.

### Problem #11 — X search pages returned few results / top-tab timeout ❌→✅

**Symptom:** crawling `x.com/search?q=...` returned only a handful of posts,
and the Top-tab URL sometimes failed with `Page.goto: Timeout 60000ms`.

**Root cause (two bugs):**
1. **X virtualizes the timeline** — only ~3-9 `article` elements stay in the
   DOM near the viewport; scrolled-past posts are unmounted, so extracting
   after scrolling yields ~6-10 posts no matter how far you scroll.
2. X search pages **never fire the `load` event** (they stream resources
   indefinitely), so `wait_until="load"` hit the 60 s cap.

**Fix:** search URLs are detected (`x.com/search` + `q=`) and handled
specially (section 3.4): `wait_until="domcontentloaded"` + a 120 s page
timeout, and a JS extractor that scrolls **one viewport at a time and
extracts on every step**, merging into a URL-deduped map — measured 60 steps
→ 80 posts, 120 steps → 290 posts on the Live tab. Single-tweet and profile
output are untouched.

---

## 7. Setup (from scratch)

```bash
cd /home/openclaw/hermesworkspace/social-media

# 1. Create venv (Python 3.12)
python3.12 -m venv venv

# 2. Install packages
venv/bin/python -m pip install crawl4ai flask playwright-stealth

# 3. Install Playwright browser (Chromium)
venv/bin/python -m playwright install chromium

# 4. Verify
venv/bin/python -c "import crawl4ai, flask, playwright; print('OK')"
```

---

## 8. Usage

### Step 1 — Log in (once, or whenever the platform logs you out)

Facebook (default):

```bash
cd /home/openclaw/hermesworkspace/social-media
venv/bin/python login.py
```

Twitter / X:

```bash
cd /home/openclaw/hermesworkspace/social-media
venv/bin/python login.py --platform twitter
```

Instagram:

```bash
cd /home/openclaw/hermesworkspace/social-media
venv/bin/python login.py --platform instagram
```

- A browser window opens on the platform's login page
  (`https://www.facebook.com/`, `https://x.com/` or
  `https://www.instagram.com/`).
- Log in manually (2FA/checkpoints work normally — it's a real browser).
- The session is saved **automatically** once the login cookie is detected
  (`c_user` for Facebook, `auth_token` for X, `sessionid` for Instagram), or
  press **Enter** to save manually.
- The browser **stays open** until you press **Enter** (or Ctrl+C) to close it.

### Step 2 — Start the crawling server

```bash
cd /home/openclaw/hermesworkspace/social-media
venv/bin/python server.py
```

Wait for `🚀 Crawl4AI সার্ভার চালু হচ্ছে http://localhost:3000`. All session
files are loaded at startup (missing ones are reported and skipped).

### Step 3 — Crawl

Facebook:

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.facebook.com/some-page-or-group"}'
```

Twitter / X:

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://x.com/some-user"}'
```

Twitter / X search (returns structured post JSON — see section 3.4):

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://x.com/search?q=automation%20services&src=typed_query&f=live", "max_scroll_steps": 120}'
```

Instagram (profile / post / Reels — see section 3.5):

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/some-user/", "max_scroll_steps": 20}'
```

---

## 9. Verification Results (2026-08-06)

Everything below was **executed and confirmed** on this machine:

| Check | Result |
|---|---|
| Headed browser launches under WSLg (`DISPLAY=:0`) | ✅ |
| Browser stays open indefinitely during manual login | ✅ (verified alive 40 s+) |
| `fb_state.json` written on Enter with valid `{cookies, origins}` | ✅ |
| Ctrl+C graceful shutdown (`Browser closed. Goodbye.`) | ✅ clean exit |
| `GET /health` → `session_loaded: true` | ✅ |
| `POST /crawl` (example.com) | ✅ `success: True`, html 559 |
| `POST /crawl` twice (event-loop reuse) | ✅ both succeeded |
| **Authenticated FB crawl of own profile** (`profile.php?id=61590946466905`) | ✅ 2 MB HTML, contains `HT Hasan`, real friend count, unread-notification count, logged-in nav (`/friends/`, `/groups/`) |
| `POST /crawl` on `facebook.com/zuck` after the scroll+full-markdown fix | ✅ 4 MB HTML, 76 KB markdown, `## Posts` section with real post text + photo links ("Benny's first 4th. Welcome to the fam 🇺🇸") |
| `cleaner.py` unit tests (`python3 test_cleaner.py`) | ✅ 27/27 assertions pass (nav, sponsored, action bars, counts, timestamps, notifications, SVG blobs, obfuscated strings, duplicates all removed; real posts kept) |
| `test_cleaner_twitter.py` (`python3 test_cleaner_twitter.py`) | ✅ 31/31 assertions pass (X nav, action bar, reply chrome, counts, timestamps, Promoted, trends, login wall, profile meta, footer, status-page chrome, Bengali UI removed; real tweets + author lines kept) |
| **Cleaning on live FB feed crawl** (`clean: true`, 2 scroll steps) | ✅ 306 lines / 58,572 chars in → **8 lines / 297 chars out (99 % removed)**; `cleaning_stats` returned; only real posts remain (author + text) |
| `clean: false` (raw markdown passthrough) | ✅ returns raw Crawl4AI markdown, `cleaning_stats: null` |

**Twitter support (added 2026-08-06):**

| Check | Result |
|---|---|
| `login.py --platform twitter` launches headed X login page | ✅ browser opens on `https://x.com/`, banner "Log in to Twitter (X) in the window now." |
| `GET /health` → `twitter_session_loaded` | ✅ `false` when `twitter_state.json` absent, `true` when present |
| `POST /crawl` with `x.com` URL, no Twitter session | ✅ `{ "error": "টুইটার সেশন পাওয়া যায়নি। আগে login.py --platform twitter চালান।" }` |
| `POST /crawl` `https://x.com/elonmusk` (stub session, 4 scroll steps) | ✅ `success: True`, `platform: "twitter"`, `html_length` 272 KB, 9,633 chars → **1,148 chars (88 % removed)**; real tweets kept (SpaceX broadcast post, "The first space economy will not look like science fiction…", author lines `@PeterDiamandis` etc.), all X chrome removed |
| `POST /crawl` `https://x.com/GeminiApp/status/2082563490431246623` (real authenticated session) | ✅ `success: True`, cleaned markdown keeps the full tweet + link + replies (6,985 chars → 1,259, 82 % removed); logged-in-only signals present (`@hasan540u`, unfollow buttons) |
| `platform` override param (`"platform": "twitter"` on a facebook.com URL) | ✅ honored — crawl ran with the Twitter session |
| `cleaner.py` Twitter path | ✅ 31/31 `test_cleaner_twitter.py` assertions pass |
| Facebook regression (final code) | ✅ `POST /crawl` `facebook.com/zuck` still `success: True`, `platform: "facebook"`, 3.86 MB HTML, 97 % noise removed, logged-in state (`Comment as HT Hasan`) intact |

**Stealth hardening (added 2026-08-06):**

| Check | Result |
|---|---|
| Fingerprint before | ❌ WebGL dead (`null` renderer), UA `Chrome/116` (engine is Chromium 151), no `chrome.runtime`, Playwright default `1080x600` viewport, headless notifications `denied` |
| Fingerprint after (headed login browser) | ✅ UA `Chrome/151.0.0.0` Linux, `webdriver` hidden, **WebGL alive** (SwiftShader), `chrome.runtime` present, `1366x768` viewport, notifications `default`, platform `Linux x86_64` |
| Fingerprint after (headless crawl + real `arun()` page) | ✅ identical to headed — consistent Linux fingerprint everywhere, `arun success: true` |
| Persistent profiles | ✅ `browser_profiles/twitter` created with real browser state (Cookies, Local State, Safe Browsing, caches) |
| `login.py --platform twitter` with stealth | ✅ headed browser opens, banner prints, stays open (timeout-killed cleanly, no orphan processes) |
| FB crawl regression (persistent + manual session injection, twice) | ✅ both `success: True`, `platform: "facebook"`, ~98 % noise removed, logged-in state detected — sequential profile reuse works |
| Twitter crawl (stub session, persistent path) | ✅ `success: True`, `platform: "twitter"`, 88 % noise removed, real tweets kept |

**Search-result extraction (added 2026-08-06):**

| Check | Result |
|---|---|
| `x.com/search?q=…&src=typed_query&f=live` (Live tab, default 60 steps) | ✅ `search: true`, 80 structured posts in ~35 s — author/text/url/timestamp/media/replies/reposts/likes all populated |
| `x.com/search?q=…&src=typed_query` (Top tab) | ✅ no more `Page.goto` timeout (`domcontentloaded` + 120 s timeout), structured posts returned |
| Volume scaling (`max_scroll_steps: 120`, Live tab) | ✅ **290 unique posts** (~90 s) — X's virtualized DOM handled by per-step extraction + URL dedupe |
| Media quality | ✅ real `pbs.twimg.com` image/video-thumb URLs only; `blob:`/`data:` filtered |
| Engagement counts | ✅ parsed from aria-labels incl. `1,234` / `1.2K` formats (e.g. 833 replies, 349 likes) |
| Ads in search | ✅ `Promoted` posts skipped |
| **Single-tweet regression** (`x.com/GeminiApp/status/…`) | ✅ response shape byte-identical to before (no `search`/`results` keys), cleaned markdown unchanged |
| FB + profile regression | ✅ both still return the original markdown response (98 % noise removed, logged in) |

**Session cookie check (logged in):** `c_user` ✅, `xs` ✅, `sb` ✅, `datr` ✅,
`fr` ✅, `wd` ✅.

---

## 10. Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| Browser flashes and closes | `DISPLAY` not set — fixed by `ensure_display()`; if it still fails, no X server is running (enable WSLg, reopen the terminal). |
| `fb_state.json` not found on server start | Run `login.py` first. |
| `twitter_state.json` not found on server start | Run `login.py --platform twitter` first. The server prints a warning and continues — Facebook crawling still works. |
| `Port 3000 is in use` | Another `server.py` is already running — use it, or stop it first. |
| Crawl returns login wall | Session expired — re-run `login.py` (add `--platform twitter` for X), log in again, then **restart `server.py`**. |
| Twitter crawl says "টুইটার সেশন পাওয়া যায়নি" | You haven't logged in for Twitter yet: `venv/bin/python login.py --platform twitter`, then restart `server.py`. |
| X crawl used the Facebook session (or vice versa) | Platform is auto-detected from the URL (`x.com`/`twitter.com` → twitter). To force it, pass `"platform": "twitter"` / `"facebook"` in the request body. |
| Crawl succeeds but no posts in the markdown | Old truncation + no-scroll bug — see Problem #8. Restart `server.py` to pick up the fix; if already restarted, raise `max_scroll_steps`. |
| Output still too noisy / raw markdown returned | The running `server.py` predates the cleaner — **restart it** (`Ctrl+C`, then `python server.py`) so it imports `cleaner.py`. Verify `cleaning_stats` appears in the response; pass `"clean": true` explicitly if it was disabled. |
| Want the raw markdown (no cleaning) | Send `"clean": false` in the request body. |
| Facebook "checkpoint"/suspicious-login screen | Log in and complete the check inside the browser; the cookie poll will detect `c_user` afterwards. |
| X shows "suspicious login" / email-code check | Same — complete it inside the headed browser; the poll detects `auth_token` afterwards. |
| X flags the login as "unusual" / restricts the account | Automation fingerprint (dead WebGL, stale UA, fresh profile) — fixed by `browser_stealth.py` (section 3.3). Wait out the temporary restriction (usually 24-48 h), then run `login.py --platform twitter` again; the persistent profile makes it look like the same device. |
| X search returns only a few posts | X virtualizes the timeline — only visible posts exist in the DOM. The search extractor captures posts while scrolling (section 3.4); raise `max_scroll_steps` (e.g. `150-300`) for more. |
| X search crawl times out | Old server before the search fix used `wait_until="load"` (which X search never fires). **Restart `server.py`** to get `domcontentloaded` + the 120 s timeout. |

---

## 11. Key Pitfalls (for future edits)

1. **`arun()` ≠ manual login.** It closes the page/context after crawling.
   Interactive flows need `browser_manager.get_page()`.
2. **0.9.2 storage APIs are renamed/broken.** Use
   `context.storage_state()` (Playwright) — never `get_storage_state()`.
3. **Headed browsers on WSL need `DISPLAY`.** Always auto-detect
   `/tmp/.X11-unix/X*`.
4. **Never cancel asyncio tasks mid-Playwright-call** — wedge the protocol.
   Use signal flags + a non-cancelled `finally` close.
5. **`server.py` reads `fb_state.json` once at startup** — restart after
   re-login.
6. **Facebook posts lazy-load on scroll.** `scan_full_page` defaults to
   `False`, so without scrolling you only get ~3 posts. Enable it with a
   generous `delay_before_return_html` — and avoid
   `wait_for="div[role='article']"` (times out on FB).
7. **Don't truncate the markdown** (e.g. `[:1000]`) — FB page chrome fills
   the first KB; post bodies live near the end under `## Posts`.
8. **FB obfuscates link text with zero-width characters** — strip
   `\u200b`-style chars when parsing post text.
9. **Clean FB markdown line-by-line, not block-by-block.** Raw FB markdown
   has almost no blank-line separators — block splitting produces one giant
   block and filters nothing. `cleaner.py` works per line; keep generic
   patterns (Tier 3) restricted to **short** lines so real post text (often
   > 160 chars) is never matched.
10. **SVG data-URIs contain escaped parens (`\(` `\)`).** A naive
    `!\[[^\]]*\]\([^)]*\)` regex stops at the first escaped `)` and leaks
    thousands of junk chars. Match the URL with `(?:[^()\\]|\\.)*`.
11. **Filter order matters:** strip image links **before** text links
    (`[text](url)`), and drop pure-URL / pure-number / separator / emoji /
    obfuscated-char lines **before** running the pattern tiers.
12. **`server.py` imports `cleaner.py` at startup** — after editing the
    cleaner, restart the server or responses keep using the old module.
13. **Twitter/X login cookie is `auth_token`** (not `c_user`) and its state
    file is `twitter_state.json`. `login.py --platform twitter` handles it;
    Facebook remains the default so old invocations behave identically.
14. **Platform is auto-detected from the URL** in `server.py`
    (`x.com`/`twitter.com` → twitter, else facebook). The request body
    `"platform"` param overrides it. Both state files are read once at
    startup — restart after re-login on either platform.
15. **`clean_markdown()` defaults to `platform="facebook"`** — the Facebook
    path (patterns, order, thresholds) is byte-for-byte the old behavior;
    `platform="twitter"` selects a separate X pattern set. Standalone n8n
    callers that don't pass `platform` get exactly what they got before.
16. **Hashtag-only lines on X** (`#Automation`) are matched on the **raw**
    line, before `_clean_line()` strips the `#` as a markdown heading —
    matching after the strip would see only `Automation` and keep it.
17. **Crawl4AI 0.9.2 persistent-context bug:** `BrowserConfig(storage_state=...)`
    crashes with `launch_persistent_context() got an unexpected keyword
    argument 'storage_state'`. Inject sessions manually instead:
    `get_page(session_id)` → `context.add_cookies()` + per-origin
    `localStorage` init scripts → `arun(session_id=...)` (session is reused).
18. **Dedicated launch path kills WebGL.** Crawl4AI hardcodes
    `--disable-gpu --disable-software-rasterizer` in `_build_browser_args()`
    (not removable via `extra_args`), so anti-bot sees a `null` WebGL
    renderer. Use `use_persistent_context=True` (+ `enable_stealth=True`),
    whose launch path keeps WebGL alive — needed for `browser_stealth.py`.
19. **playwright-stealth defaults are Windows-biased.** Stock
    `navigator_platform_override="Win32"` contradicts a Linux UA. Patch the
    `Stealth.__init__` defaults (platform → `Linux x86_64`, webgl/UA evasions
    off) in `browser_stealth.py` before any browser is created.
20. **Persistent profiles mean real state.** `browser_profiles/` accumulates
    history/cache/cookies (login profiles hold the live FB/X sessions).
    Delete a profile dir to reset a platform's browser to a fresh state.
21. **X virtualizes its timeline** — only ~3-9 articles stay in the DOM near
    the viewport; scrolled-past posts are unmounted. Extracting after
    scrolling yields only a handful of posts. For search pages, scroll one
    viewport at a time and extract on every step, merging by status URL.
22. **X search pages never fire `load`** — `wait_until="load"` times out at
    60 s. Use `wait_until="domcontentloaded"` + a longer `page_timeout`
    (direct `CrawlerRunConfig` construction isn't capped by Crawl4AI's
    untrusted-input cap).
