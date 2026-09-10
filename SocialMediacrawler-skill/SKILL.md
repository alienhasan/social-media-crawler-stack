---
name: SocialMediacrawler
description: Operate and maintain the authenticated Facebook and Twitter/x Crawling Server (Crawl4AI-based) that crawls profiles, pages, groups, and posts, tweets, twitter search results and returns cleaned Markdown via an HTTP API.
tags: [facebook, Twitter, X, Tweet crawling, crawl4ai, scraping]
related_skills: []
---
# Role

You are an expert Python backend engineer and Crawl4AI specialist responsible for operating and testing the Social Media Crawler server.

---

# Goal

Your objectives are to:

- Start the crawler server.
- Verify the server is healthy.
- Crawl **exactly one** Facebook or Twitter/X page per request.
- Support Twitter/X search pages.
- Return the complete JSON response.
- Follow the project workflow without modifying the project unless explicitly requested.

---

# Project

Project directory:

/home/openclaw/hermesworkspace/social-media

Main files:

- login.py
- server.py
- cleaner.py
- fb_state.json
- twitter_state.json

Authentication:

- Facebook requires `fb_state.json`
- Twitter/X requires `twitter_state.json`

If the required session is missing or expired:

1. Run `login.py`
2. Log in manually.
3. Restart `server.py`.

---

# Rules

Always:

- Check the server health before crawling.
- Crawl **only one URL per request**.
- Wait for the current crawl to finish before starting another.
- Return the complete JSON response.

Never:

- Crawl Facebook and Twitter/X in the same request.
- Send multiple URLs in one request.
- Send concurrent crawl requests.
- Modify the project unless explicitly instructed.

---

# Start the Server

```bash
cd /home/openclaw/hermesworkspace/social-media

venv/bin/python server.py
```

Server:

```
http://localhost:3000
```

Wait until the server is fully started before sending any request.

---

# Check Server Health

```bash
curl http://localhost:3000/health
```

Example:

```json
{
  "status": "ok",
  "session_loaded": true,
  "twitter_session_loaded": true,
  "port": 3000
}
```

Only continue if:

- `status == "ok"`

Otherwise, stop and report the problem.

---

# Crawl a Facebook Page

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url":"https://www.facebook.com/your-page-or-group"
  }'
```

---

# Crawl a Twitter/X Profile or Post

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url":"https://x.com/username/status/123456789"
  }'
```

---

# Crawl Twitter/X Search Results

Supported URLs:

Top Results

```
https://x.com/search?q=<QUERY>&src=typed_query
```

Live Results (live means latest results)

```
https://x.com/search?q=<QUERY>&src=typed_query&f=live
```

Examples:

```
https://x.com/search?q=AI&src=typed_query

https://x.com/search?q=AI&src=typed_query&f=live
```

Top search request:

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url":"https://x.com/search?q=AI&src=typed_query"
  }'
```

Live/latest search results request:

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url":"https://x.com/search?q=AI&src=typed_query&f=live"
  }'
```

To collect more posts:

```bash
curl -X POST http://localhost:3000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url":"https://x.com/search?q=AI&src=typed_query&f=live",
    "max_scroll_steps":120
  }'
```

Twitter search responses return structured JSON containing fields such as:

- author
- text
- url
- timestamp
- media
- replies
- reposts
- likes

---

# Workflow

1. Start the server.
2. Check `/health`.
3. Verify the required login session exists.
4. Crawl **one URL**.
5. Wait for the crawl to complete.
6. Return the full JSON response.
7. Repeat for the next page if needed.

---

# Error Handling

- If the server is not healthy, stop.
- If the required session is missing, tell the user to run `login.py` and restart the server.
- Do not continue until the issue is resolved.
