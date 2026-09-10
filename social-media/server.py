import asyncio
import json
import os
import uuid
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from cleaner import clean_markdown
from browser_stealth import stealth_kwargs, PROFILES_DIR

app = Flask(__name__)

# persistent server profile: real-browser fingerprint (WebGL alive, history/cache)
SERVER_PROFILE_DIR = os.path.join(PROFILES_DIR, "server")


def _build_localstorage_scripts(storage_state):
    """প্রতিটি origin-এর saved localStorage inject করার জন্য init script বানায়।"""
    scripts = []
    for origin in (storage_state or {}).get("origins") or []:
        pairs = {
            item.get("name"): item.get("value")
            for item in (origin.get("localStorage") or [])
            if item.get("name") is not None
        }
        if not pairs:
            continue
        parts = "".join(
            f"localStorage.setItem({json.dumps(k)},{json.dumps(v)});"
            for k, v in pairs.items()
        )
        scripts.append(f"try{{{parts}}}catch(e){{}}")
    return scripts


async def _inject_session(context, storage_state):
    """Persistent context-এ saved session (cookies + localStorage) inject করে।

    Crawl4AI 0.9.2-এর persistent-context পথে BrowserConfig(storage_state=...)
    দিলে crash হয় (launch_persistent_context storage_state সাপোর্ট করে না),
    তাই সেশন এখানে ম্যানুয়ালি inject করা হয়।
    """
    cookies = (storage_state or {}).get("cookies") or []
    if cookies:
        await context.add_cookies(cookies)
    for script in _build_localstorage_scripts(storage_state):
        await context.add_init_script(script)

# সেশন ফাইল লোড করুন — Facebook
try:
    with open("fb_state.json", "r") as f:
        STORAGE_STATE = json.load(f)
    print("✅ সেশন লোড হয়েছে (fb_state.json)")
except FileNotFoundError:
    print("⚠️ fb_state.json পাওয়া যায়নি! আগে login.py চালান।")
    STORAGE_STATE = None

# সেশন ফাইল লোড করুন — Twitter/X
try:
    with open("twitter_state.json", "r") as f:
        TWITTER_STORAGE_STATE = json.load(f)
    print("✅ টুইটার সেশন লোড হয়েছে (twitter_state.json)")
except FileNotFoundError:
    print("⚠️ twitter_state.json পাওয়া যায়নি! আগে login.py --platform twitter চালান।")
    TWITTER_STORAGE_STATE = None

# সেশন ফাইল লোড করুন — Instagram
try:
    with open("ig_state.json", "r") as f:
        INSTAGRAM_STORAGE_STATE = json.load(f)
    print("✅ ইনস্টাগ্রাম সেশন লোড হয়েছে (ig_state.json)")
except FileNotFoundError:
    print("⚠️ ig_state.json পাওয়া যায়নি! আগে login.py --platform instagram চালান।")
    INSTAGRAM_STORAGE_STATE = None


def detect_platform(url: str) -> str:
    """URL দেখে platform চেনে:
    x.com / twitter.com → twitter, instagram.com → instagram, বাকি সব → facebook"""
    u = (url or "").lower()
    if "x.com" in u or "twitter.com" in u:
        return "twitter"
    if "instagram.com" in u or "instagr.am" in u:
        return "instagram"
    return "facebook"


def is_twitter_search_url(url: str) -> bool:
    """URL টুইটার (X) search result page কিনা চেনে।"""
    u = (url or "").lower()
    if "x.com/search" not in u and "twitter.com/search" not in u:
        return False
    return "q=" in u


def search_query(url: str) -> str:
    """Search URL থেকে q= query বের করে।"""
    qs = parse_qs(urlparse(url or "").query)
    return qs.get("q", [""])[0]


# ---------------------------------------------------------------------------
# Twitter (X) search-result extraction.
# Search pages return structured post objects instead of cleaned markdown:
#   {author, text, url, timestamp, media, replies, reposts, likes}
# X virtualizes the timeline: only ~3-9 articles stay in the DOM near the
# viewport, older ones are unmounted as you scroll. So the script scrolls
# one viewport at a time and EXTRACTS ON EVERY STEP, merging into a
# URL-deduped map — this captures every post as it passes through.
# No backslashes by design — paste-safe.
# ---------------------------------------------------------------------------
TWITTER_SEARCH_EXTRACT_JS = r"""async (opts) => {
  const maxSteps = (opts && opts.max_steps) || 60;
  const delayMs = (opts && opts.scroll_delay_ms) || 700;
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const parseNum = (s) => {
    if (!s) return 0;
    const m = s.replace(/,/g, '').match(/([0-9]+(?:[.][0-9]+)?)[ \t]*([kKmMbB])?/);
    if (!m) return 0;
    let n = parseFloat(m[1]);
    const suf = (m[2] || '').toUpperCase();
    if (suf === 'K') n *= 1000;
    else if (suf === 'M') n *= 1000000;
    else if (suf === 'B') n *= 1000000000;
    return Math.round(n);
  };
  const isAd = (a) => Array.from(a.querySelectorAll('span')).some((s) => s.textContent.trim() === 'Promoted');
  const usableMedia = (src) => (src && src.indexOf('http') === 0 && src.indexOf('blob:') !== 0 && src.indexOf('data:') !== 0) ? src : null;
  const posts = new Map(); // url -> post
  const extract = () => {
    document.querySelectorAll('article[data-testid="tweet"]').forEach((a) => {
      if (isAd(a)) return;
      const userName = a.querySelector('[data-testid="User-Name"]');
      const link = (userName && userName.querySelector('a[href*="/status/"]')) || a.querySelector('a[href*="/status/"]');
      if (!link) return;
      const href = (link.getAttribute('href') || '').split('?')[0].split('#')[0];
      const parts = href.split('/'); // ["", "handle", "status", "id"]
      if (parts.length < 4 || parts[2] !== 'status') return;
      const url = 'https://x.com' + href;
      if (posts.has(url)) return;
      const textEl = a.querySelector('[data-testid="tweetText"]');
      const text = textEl ? textEl.innerText.trim() : '';
      const timeEl = a.querySelector('time');
      const timestamp = timeEl ? (timeEl.getAttribute('datetime') || timeEl.innerText.trim()) : '';
      const media = [];
      a.querySelectorAll('img[src*="/media/"]').forEach((img) => {
        const src = usableMedia(img.getAttribute('src'));
        if (src && media.indexOf(src) === -1) media.push(src);
      });
      a.querySelectorAll('video').forEach((v) => {
        const src = usableMedia(v.getAttribute('poster') || v.getAttribute('src') || (v.querySelector('source') && v.querySelector('source').getAttribute('src')));
        if (src && media.indexOf(src) === -1) media.push(src);
      });
      const count = (el) => {
        if (!el) return 0;
        return parseNum((el.getAttribute('aria-label') || '') + ' ' + (el.getAttribute('data-count') || ''));
      };
      posts.set(url, {
        author: '@' + parts[1],
        text,
        url,
        timestamp,
        media,
        replies: count(a.querySelector('[data-testid="reply"]')),
        reposts: count(a.querySelector('[data-testid="retweet"]')),
        likes: count(a.querySelector('[data-testid="like"]')),
      });
    });
  };
  // Wait for the timeline shell to boot, then capture the first batch
  await sleep(delayMs * 2);
  extract();
  // Scroll one viewport at a time, extracting on every step (virtualized DOM)
  let lastHeight = 0;
  let stable = 0;
  for (let i = 0; i < maxSteps; i++) {
    window.scrollBy(0, window.innerHeight);
    await sleep(delayMs);
    extract();
    const h = document.documentElement.scrollHeight;
    if (h === lastHeight) { if (i >= 4) { stable += 1; if (stable >= 3) break; } }
    else { stable = 0; lastHeight = h; }
  }
  return Array.from(posts.values());
}"""


async def crawl_url(target_url, max_scroll_steps=None, clean=True, extra_patterns=None, platform=None):
    """একটি URL ক্রল করে পরিষ্কার করা content রিটার্ন করে"""
    if platform not in ("facebook", "twitter", "instagram"):
        platform = detect_platform(target_url)

    # Twitter (X) search pages: structured extraction + more scrolling
    is_search = platform == "twitter" and is_twitter_search_url(target_url)
    # Instagram-এর profile/explore পেজও lazy-load — বেশি scroll লাগে
    is_instagram = platform == "instagram"
    if max_scroll_steps is None:
        if is_search:
            max_scroll_steps = 60
        elif is_instagram:
            max_scroll_steps = 20
        else:
            max_scroll_steps = 15

    if platform == "twitter":
        storage = TWITTER_STORAGE_STATE
        if not storage:
            return {"error": "টুইটার সেশন পাওয়া যায়নি। আগে login.py --platform twitter চালান।"}
    elif platform == "instagram":
        storage = INSTAGRAM_STORAGE_STATE
        if not storage:
            return {"error": "ইনস্টাগ্রাম সেশন পাওয়া যায়নি। আগে login.py --platform instagram চালান।"}
    else:
        storage = STORAGE_STATE
        if not storage:
            return {"error": "সেশন পাওয়া যায়নি। আগে login.py চালান।"}

    browser_config = BrowserConfig(
        headless=True,  # সার্ভার মোডে headless চালাবেন
        **stealth_kwargs(user_data_dir=SERVER_PROFILE_DIR)  # real-browser fingerprint
    )

    # Facebook/Twitter/Instagram posts লোড হয় lazily (scroll করলে)। তাই:
    # - wait_until="load": পেজ শেল লোড হওয়া পর্যন্ত অপেক্ষা
    # - delay_before_return_html: posts render হওয়ার জন্য সময় দিন
    # - scan_full_page + scroll: নিচে স্ক্রল করে বেশি posts লোড করান
    #   (search pages-এ scroll নিজের JS দিয়ে হয় — Crawl4AI-এর scroll X-এ তাড়াতাড়ি থেমে যায়)
    session_id = f"crawl-{uuid.uuid4().hex[:12]}"
    run_config = CrawlerRunConfig(
        verbose=False,
        # search pages-এ "load" কখনো শেষ হয় না (X সারাক্ষণ লোড করে) → domcontentloaded
        # Instagram-ও React SPA: "load" অনির্দিষ্টকাল ধরে চলতে পারে → domcontentloaded
        wait_until="domcontentloaded" if (is_search or is_instagram) else "load",
        page_timeout=120000 if is_search else (90000 if is_instagram else 60000),
        delay_before_return_html=2.5 if is_search else (4.0 if is_instagram else 3.0),
        # search pages-এ scroll নিজের JS দিয়ে হয় — Crawl4AI-এর scroll X-এ তাড়াতাড়ি থেমে যায়
        scan_full_page=not is_search,
        scroll_delay=0.5 if is_instagram else 0.4,
        max_scroll_steps=0 if is_search else max_scroll_steps,
        session_id=session_id,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # saved session (cookies + localStorage) আগে থেকে context-এ inject করুন
        _, context = await crawler.crawler_strategy.browser_manager.get_page(
            CrawlerRunConfig(session_id=session_id, verbose=False)
        )
        await _inject_session(context, storage)
        result = await crawler.arun(
            url=target_url,
            config=run_config
        )

        if result.success and is_search:
            # live page থেকে structured post data বের করুন (JS নিজে scroll + extract করে)
            page, _ = await crawler.crawler_strategy.browser_manager.get_page(run_config)
            posts = await page.evaluate(
                TWITTER_SEARCH_EXTRACT_JS,
                {"max_steps": max_scroll_steps, "scroll_delay_ms": 700},
            )
            return {
                "success": True,
                "url": target_url,
                "platform": platform,
                "search": True,
                "query": search_query(target_url),
                "result_count": len(posts),
                "results": posts,
            }

        if result.success:
            markdown = result.markdown if result.markdown else None
            cleaning_stats = None
            if markdown and clean:
                cleaned = clean_markdown(markdown, extra_patterns=extra_patterns, platform=platform)
                markdown = cleaned.pop("cleaned")
                cleaning_stats = cleaned
            return {
                "success": True,
                "url": target_url,
                "platform": platform,
                "html_length": len(result.html),
                "markdown": markdown,  # clean=True হলে noise বাদ দেওয়া content
                "cleaning_stats": cleaning_stats,  # কতটা বাদ পড়ল (None = clean চালু নেই)
                "screenshot": result.screenshot if result.screenshot else None
            }
        else:
            return {
                "success": False,
                "url": target_url,
                "platform": platform,
                "error": result.error_message
            }

@app.route('/crawl', methods=['POST'])
def crawl():
    """POST request-এর মাধ্যমে URL ক্রল করুন"""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({"error": "দয়া করে JSON-এ 'url' পাঠান"}), 400

    target_url = data['url']
    # optional: কতগুলো scroll step নিতে হবে (বেশি = বেশি posts, ধীর)
    # না দিলে crawl_url নিজেই ঠিক করে: সাধারণ 15, টুইটার সার্চ 40
    max_scroll_steps = int(data['max_scroll_steps']) if 'max_scroll_steps' in data else None
    # optional: noise cleaner চালু/বন্ধ (ডিফল্ট True)
    clean = data.get('clean', True)
    if isinstance(clean, str):
        clean = clean.lower() not in ("false", "0", "no")
    # optional: অতিরিক্ত noise প্যাটার্ন (regex list) — নিজের মতো ফিল্টার যোগ করতে
    extra_patterns = data.get('exclude_patterns') or None
    # optional: platform ঠিক করে দেওয়া ("facebook"/"twitter"/"instagram"); না দিলে URL থেকে চেনা হয়
    platform = data.get('platform')
    if platform not in ("facebook", "twitter", "instagram"):
        platform = None

    # Asynchronous ফাংশনটি synchronous ভাবে চালান
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(
        crawl_url(target_url, max_scroll_steps, clean, extra_patterns, platform)
    )
    loop.close()

    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    """সার্ভার চালু আছে কিনা চেক করুন"""
    return jsonify({
        "status": "ok",
        "session_loaded": STORAGE_STATE is not None,
        "twitter_session_loaded": TWITTER_STORAGE_STATE is not None,
        "instagram_session_loaded": INSTAGRAM_STORAGE_STATE is not None,
        "port": 3000
    })

if __name__ == '__main__':
    print("🚀 Crawl4AI সার্ভার চালু হচ্ছে http://localhost:3000")
    print("📌 POST /crawl - { 'url': 'https://facebook.com/some-page' }")
    print("📌 POST /crawl - { 'url': 'https://x.com/some-user' } (টুইটার)")
    print("📌 POST /crawl - { 'url': 'https://www.instagram.com/some-user/' } (ইনস্টাগ্রাম)")
    print("📌 GET /health - সার্ভার স্ট্যাটাস চেক")
    app.run(host='0.0.0.0', port=3000, debug=False)
