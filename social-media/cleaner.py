# -*- coding: utf-8 -*-
"""
cleaner.py — Crawl4AI markdown আউটপুট থেকে noise ডেটা পরিষ্কার করার মডিউল।

Crawl4AI-এর markdown-এ সাধারণত প্রচুর অপ্রয়োজনীয় ডেটা থাকে:
  - Facebook-এর navigation/sidebar (Home, Watch, Marketplace, Groups, ...)
  - "Suggested for you", "Sponsored", "People you may know" — suggestion/ad block
  - লগইন ও কুকি কনসেন্ট prompt
  - পোস্টের action bar ("Like Comment Share", "Write a comment", ...)
  - লিংক-মোড়ানো menu item: [Friends](https://facebook.com/friends/)
  - বিশাল data-URI image ব্লব: ![](data:image/svg+xml,....) (reaction icon)
  - notification alert ("We noticed a new login...", "You can help grow...")
  - image-post placeholder: "m.me Photos from X's post ..." (obfuscated string সহ)
  - শুধু সংখ্যা (like/reaction count: 1.2K, 270), শুধু URL, ছোট খণ্ড, ডুপ্লিকেট লাইন

ফিল্টার ৩ ধাপে:
  TIER 1 (STRONG_LABELS)     — লাইন এই দিয়ে শুরু হলে সবসময় বাদ
  TIER 2 (ALL_LINE_PATTERNS) — লাইনের যেকোনো জায়গায়, যেকোনো দৈর্ঘ্যে বাদ
  TIER 3 (NOISE_PATTERNS)    — ছোট লাইনে (SHORT_LINE_MAX_CHARS-এর কম) ম্যাচ হলে বাদ

clean_markdown() পরিষ্কার content আর পরিসংখ্যান রিটার্ন করে।
"""

import re

# ---------------------------------------------------------------------------
# TIER 1 — Strong label: লাইন এই দিয়ে শুরু হলে পুরো লাইন বাদ (লম্বা sponsored
# post-এর টেক্সটও বাদ যায় — এগুলো promo, lead-gen-এ noise)
# ---------------------------------------------------------------------------
STRONG_LABELS = [
    r"^sponsored\b",
    r"^স্পনসরড\b",
    r"^স্পনসর\b",
    r"^suggested for you",
    r"^people you may know",
    r"^you might like",
    r"^পরামর্শ",
    r"^তুমি (হয়তো|হতে পারে) পছন্দ",
    r"^আপনি (হয়তো|হতে পারে) পছন্দ",
    r"^পরিচিত মানুষ",
    r"^recommended",
    r"^log in to facebook",
    r"^create new account",
    r"^নতুন অ্যাকাউন্ট",
]

# ---------------------------------------------------------------------------
# TIER 2 — Medium-strong: লাইনের যেকোনো জায়গায় ম্যাচ = বাদ (দৈর্ঘ্য নির্বিশেষে)।
# এগুলো FB-এর chrome/notification টেক্সট — real post-এ প্রায় আসে না।
# ---------------------------------------------------------------------------
ALL_LINE_PATTERNS = [
    r"photos from",
    r"m\.me",
    r"mobile uploads",
    r"verified account",
    r"learn more",
    r"we noticed a new login",
    r"you don't usually use",
    r"device or location",
    r"your full control",
    r"was removed",
    r"you can help grow",
    r"inviting your friends",
    r"create an ad",
    r"your business is ready",
    r"what's on your mind",
    r"create a post",
    r"feed posts",
    r"facebook menu",
    r"your shortcuts",
    r"see previous notifications",
    r"find friends",
    r"number of unread notifications",
    r"^unread",
    r"^turn on notifications",
    r"see translation",
    r"অনুবাদ দেখুন",
    r"^all reactions$",
]

# ---------------------------------------------------------------------------
# TIER 3 — ছোট লাইনে (SHORT_LINE_MAX_CHARS-এর কম) ম্যাচ = বাদ।
# বড় লাইনে real post text থাকতে পারে, তাই বড় লাইনে শুধু TIER 1/2 প্রযোজ্য।
# ---------------------------------------------------------------------------
SHORT_LINE_MAX_CHARS = 160

NOISE_PATTERNS = [
    # --- English: navigation / chrome ---
    r"^\s*(home|watch|marketplace|groups?|pages?|reels?|feeds?|videos?|memories|saved|events?|friends?|notifications?|messenger|menu|search|settings?|help|logout|log\s?in|sign\s?up|register|open|copy link|embed|report|edit|delete|pin|unpin|privacy|terms|advertising|more)\s*$",
    r"^(home|watch|marketplace|groups?|pages?|reels?|feeds?|videos?|memories|saved|events?|friends?|notifications?|messenger)(\s*[\s|,·•/&]+\s*(home|watch|marketplace|groups?|pages?|reels?|feeds?|videos?|memories|saved|events?|friends?|notifications?|messenger))+$",
    r"see more",
    r"see all",
    r"view all",
    r"^(new|earlier|all|unread)\s*$",
    r"^follow(ers?)?\s*$",
    r"^\s*(like|comment|share|react|send|save)\s*$",
    r"^(like|comment|share|react)\b.*\b(like|comment|share|react)",
    r"top comments",
    r"most relevant",
    r"write (a )?comment",
    r"press enter to post",
    r"^\d+\s*(comments?|shares?|reactions?|replies?)\s*$",
    r"^view \d+\s*(comments?|shares?|reactions?|replies?)\s*$",
    r"^\d+\s*(h|hr|hrs|hours?|m|min|mins?|d|days?)\s*ago\s*$",
    r"^\d{1,4}\s*(m|h|d|w|mo|y)\s*$",
    r"^(just now|yesterday|today)\s*$",
    r"cookie",
    r"privacy policy",
    r"terms? of service",
    r"ad\s?choices",
    r"allow (all |essential |optional )?cookies?",
    r"forgotten password",
    r"english \(us\)",
    r"facebook\.com/\S*\s*$",
    # --- Bengali: navigation / chrome ---
    r"লগ\s?ইন",
    r"সাইন\s?আপ",
    r"গোপনীয়তা নীতি",
    r"শর্তাবলী",
    r"কুকি",
    r"^ফলো(য়ার)?\s*$",
    r"মন্তব্য লিখুন",
    r"আরও দেখুন",
    r"সব দেখুন",
    r"^\s*(লাইক|কমেন্ট|শেয়ার|প্রতিক্রিয়া|পাঠান|সেভ)\s*$",
    r"^(লাইক|কমেন্ট|শেয়ার|প্রতিক্রিয়া)\b.*\b(লাইক|কমেন্ট|শেয়ার|প্রতিক্রিয়া)",
    r"^সব মন্তব্য$",
    r"^প্রাসঙ্গিক$",
    r"^(এখনই|গতকাল|আজ)\s*$",
    r"^\d+\s*(ঘণ্টা|ঘন্টা|মিনিট|দিন)\s*আগে\s*$",
]

# ---------------------------------------------------------------------------
# TWITTER (X) tiers — টুইটার/এক্স-এর chrome Facebook-এর থেকে আলাদা, তাই আলাদা
# pattern সেট। clean_markdown(platform="twitter") দিলে এগুলো ব্যবহৃত হয়;
# ডিফল্ট platform="facebook" — আগের মতোই Facebook pattern চলে।
# ---------------------------------------------------------------------------
TWITTER_STRONG_LABELS = [
    r"^promoted\b",              # X-এর ad label ("Promoted")
    r"^trending now",
    r"^trends for you",
    r"^what['’\u2019]s happening",
    r"^who to follow",
    r"^new to x\??",
    r"^already have an account\??",
    r"^sign up now",
    r"^sign in to x",
    r"^log in to x",
    r"^sign in to twitter",
    r"^log in to twitter",
    r"^followed by\b",           # "Followed by 1,234 people you follow"
    r"^replying to @",           # reply-এর উপরের chrome লাইন
    r"^replied to @",
    r"^show this thread",
    r"^show more replies",
    r"^show additional replies",
    r"^load more",
    r"^you might like",
]

TWITTER_ALL_LINE_PATTERNS = [
    r"terms of service",
    r"privacy policy",
    r"cookie policy",
    r"help center",
    r"developer agreement",
    r"ad\s?choices",
    r"show this thread",
    r"show more replies",
    r"show additional replies",
    r"load more",
    r"you might like",
    r"who to follow",
    r"followed by\b",
    r"replying to @",
    r"joined [a-z]+ \d{4}",      # profile meta: "Joined January 2023"
]

TWITTER_NOISE_PATTERNS = [
    # --- English: nav / tabs ---
    r"^\s*(for you|following|followers?|posts?|tweets?|explore|notifications|messages|bookmarks|lists|premium|verified|grok|chat|creator studio|accessibility|profile|home|search|settings|help|more|logout|log\s?out|switch accounts|add another account)\s*$",
    r"^(for you|following|explore|notifications|messages|bookmarks|lists)\s*[·|]\s*(for you|following|explore|notifications|messages|bookmarks|lists)\s*$",
    r"^(home|explore|notifications|follow|chat|grok|bookmarks|creator studio|premium|profile){2,}\s*$",  # concatenated nav ("HomeExploreNotifications…")
    # --- English: action bar ---
    r"^\s*(reply|repost|retweet|quote|like|view|bookmark|share|copy link|embed|report|block|unblock|mute|unmute|unfollow|follow|follow back)\s*$",
    r"^(reply|repost|retweet|quote|like|view|bookmark|share)\b.*\b(reply|repost|retweet|quote|like|view|bookmark|share)\b",
    r"^\s*(show more|show this thread|show more replies|show additional replies|load more|see more|see all|view all)\s*$",
    r"^\s*ad\s*$",
    r"^\s*promoted\s*$",
    r"^\s*verified( organizations?| orgs?)?\s*$",
    r"^\s*subscribe\s*$",
    r"^\s*joined\s*$",
    # --- English: sidebar / trends / login wall ---
    r"^\s*trending\s*$",
    r"^trending in\b",
    r"^\s*trends for you\s*$",
    r"^\s*what['’\u2019]s happening\s*$",
    r"^\s*who to follow\s*$",
    r"^\s*new to x\??\s*$",
    r"^\s*already have an account\??\s*$",
    r"^\s*sign up now\s*$",
    r"^\s*(log|sign) in to x\s*$",
    r"^\s*(log|sign) in to twitter\s*$",
    r"^log in\s*sign up\s*$",        # login-wall header ("Log inSign up")
    r"^terms\s*·\s*privacy\s*·\s*cookies",   # footer ("Terms·Privacy·Cookies·…")
    r"^scan to get the app\s*$",     # X QR promo
    r"^[\w\s.'-]+ \(@\w+\)\s*/\s*x\s*$",  # page title ("Elon Musk (@elonmusk) / X")
    # --- English: status-page chrome (tweet detail pages) ---
    r"^to view keyboard shortcuts",  # "To view keyboard shortcuts, press question mark"
    r"^view keyboard shortcuts\s*$",
    r"^see new posts\s*$",
    r"^conversation\s*$",
    r"^view quotes\s*$",
    r"^post your reply\s*$",
    r"^everyone can reply\s*$",
    r"^relevant people\s*$",
    r"^click to (un)?follow\b",
    r"^is hosting\s*$",
    r"^.+ · trending\s*$",           # trending-list items ("Politics · Trending")
    # --- English: counts / stats / timestamps ---
    r"^\d[\d,.]*[KMB]?\s*(likes?|views?|reposts?|retweets?|replies?|quotes?|bookmarks?|followers?|following|listeners?|members?)?\s*$",
    r"^\d[\d,.]*[KMB]?\s+(posts|followers|following)\s*$",
    r"^\d[\d,.]*[KMB]?\s*(following|followers|subscriptions|posts)\b",  # profile stat line (concatenated)
    r"^(posts|replies|media|likes|articles|highlights){2,}\s*$",        # concatenated profile tabs ("PostsPosts")
    r"^\d{1,2}:\d{2}\s*(:\d{2})?\s*/\s*\d{1,2}:\d{2}\s*(:\d{2})?\s*$",  # media duration ("00:00 / 01:05:09")
    r"^\s*·?\s*\d{1,3}\s*[smhdwy]\s*·?\s*$",
    r"^\d{1,3}\s*(s|sec|secs|seconds?|m|min|mins|minutes?|h|hr|hrs|hours?|d|days?|w|weeks?|mo|months?|y|yrs?|years?)\s*ago\s*$",
    r"^(just now|now|yesterday|today)\s*$",
    r"^[A-Za-z]{3}\s+\d{1,2}\s*$",
    r"^[A-Za-z]{3}\s+\d{1,2},\s*\d{4}\s*$",
    r"^\d{1,2}:\d{2}\s*(AM|PM|am|pm)?\s*$",
    r"^\s*·\s*$",
    r"^\s*·\s*·\s*$",
    # --- Bengali: X-এর বাংলা UI ---
    r"^\s*(অনুসরণ|ফলো)\s*$",
    r"^\s*অনুসরণ করুন\s*$",
    r"^\s*ফলো করুন\s*$",
    r"^\s*রিপোস্ট\s*$",
    r"^\s*উত্তর দিন\s*$",
    r"^\s*লাইক\s*$",
    r"^\s*বুকমার্ক\s*$",
    r"^\s*শেয়ার\s*$",
    r"^\s*দেখুন\s*$",
    r"^\s*উদ্ধৃতি\s*$",
    r"^\s*(আরও|আরো) দেখুন\s*$",
    r"^\s*ট্রেন্ডিং\s*$",
    r"^\s*কী ঘটছে\s*$",
    r"^\s*এক্সপ্লোর\s*$",
    r"^\s*নোটিফিকেশন\s*$",
    r"^\s*বার্তা\s*$",
    r"^\s*তালিকা\s*$",
    r"^\s*প্রোফাইল\s*$",
    r"^\s*সাইন আপ\s*$",
    r"^\s*লগ ইন\s*$",
    r"^\s*অনুসরণকারী\s*$",
    r"^\s*অনুসরণ করছেন\s*$",
    r"^\s*সাবস্ক্রাইব\s*$",
    r"^\s*যাচাইকৃত\s*$",
]

# ---------------------------------------------------------------------------
# INSTAGRAM tiers — ইনস্টাগ্রামের chrome FB/X থেকে আলাদা, তাই আলাদা pattern সেট।
# clean_markdown(platform="instagram") দিলে এগুলো ব্যবহৃত হয়।
# ---------------------------------------------------------------------------
INSTAGRAM_STRONG_LABELS = [
    r"^log in\b",                     # login wall / "Log in to like or comment"
    r"^log into instagram",
    r"^sign up\b",
    r"^create an account or log in",
    r"^switch accounts?",
    r"^edit profile",
    r"^share profile",
    r"^add a comment",
    r"^see photos\b.*\bfrom\b",       # "See photos and videos from <user>" /
                                      # "See photos, videos and more from <user>"
    r"^never miss a post",
    r"^something went wrong",
    r"^suggested for you",
    r"^more posts from",
    r"^view more on instagram",
    r"^discover people",
    r"^accounts you\b",               # "Accounts you follow" / "Accounts you might like"
    r"^meta verified",
    r"^instagram lite",
    r"^contact uploading (?:&|and) non-users",
    r"^threads terms",
    r"^see everyday moments from your close friends",
]

INSTAGRAM_ALL_LINE_PATTERNS = [
    r"log in to like or comment",
    r"create an account or log in",
    r"see photos\b.*\bfrom\b",
    r"never miss a post",
    r"more posts from",
    r"view more on instagram",
    r"instagram lite",
    r"meta verified",
    r"threads terms",
    r"see translation",
    r"অনুবাদ দেখুন",
    r"load more comments",
    r"©\s*\d{4}\s*instagram from meta",   # footer copyright
    r"contact uploading (?:&|and) non-users",
    r"by continuing, you agree",          # login-interstitial consent line
    r"terms of use and privacy policy",
    r"instagram from meta",
    r"instagram\s?log\s?in",              # concatenated wall header "InstagramLog in"
    r"instagram\s?sign\s?up",
]

INSTAGRAM_NOISE_PATTERNS = [
    # --- English: nav / tabs ---
    r"^\s*(home|search|explore|reels?|messages?|notifications?|create|profile|threads|more|settings|your activity|saved|close friends|switch appearance|log out|meta ai|ai studio|archive|insights|professional dashboard|ad tools|supervision|monetization|orders and earnings|crossposting|not interested|about this account|block|restrict|unfollow|copy profile url)\s*$",
    r"^(home|search|explore|reels|messages|notifications|create|profile|threads|more){2,}\s*$",   # concatenated nav
    r"^(posts|reels|tagged|photos|videos|saved|reposts|followers|following){2,}\s*$",            # concatenated profile tabs
    # logged-in nav rail renders icon-alt + label -> "Reels Reels", "Search Search"
    r"^((?:home|search|explore|reels|messages|notifications|create|profile|threads|more|settings))\s+\1\s*$",
    r"^\s*(new post|create)\s+create\s*$",
    r"^\s*settings\s+(more|less)\s*$",
    r"^\s*also from meta\b",
    r"^\s*instagram recommended\b",
    r"^\s*similar accounts\s*$",
    r"^\s*original audio\s*$",
    r"^\s*audio is muted\b",
    r"^\s*turn on notifications\b",
    r"^\s*turn on\s*not now\s*$",
    r"^\s*know right away when people\b",
    r"^\s*verified and\b",
    r"^.{0,40}verified\s*$",           # "Sonakshi SinhaVerified" (badge glued to name)
    # --- English: action bar ---
    r"^\s*(like|unlike|comment|share|send|save|saved|reply|embed|report|copy link|tag|remix|use audio|add to story|pin|unpin|edit|delete|translate|translation|cancel|back|next|done)\s*$",
    r"^(like|comment|share|save|send)\b.*\b(like|comment|share|save|send)\b",
    r"^\s*(follow|following|follow back|followers?|requested|message|subscribe|subscribed|verified|not verified|suggested for you|see all|see more|view all|show more|view more|liked by|lIked by|and others)\s*$",
    r"^(liked by|followed by)\b.*\b(and \d+ others?|others)\s*$",
    r"^add a comment\s*$",
    r"^post\s*$",
    r"^more options\s*$",
    r"^threads [\w.@]{2,30}\s*$",      # "Threads nikebasketball" (app CTA + handle)
    r"^[\w.@]{1,30}verified\b.*$",     # "nikeVerified 1w" (author + badge + time glued)
    r"^[\w.@]+ and \d+ others?\s*$",   # "nike and 2 others"
    r"^\s*(english|english \(uk\)|english \(us\))\s*$",
    # --- icon alt-text (Crawl4AI surfaces SVG alt attributes as lines) ---
    r"^[\w\s,.'-]{0,30}\bicon\s*$",              # "Down chevron icon", "Search icon"
    r"^\s*(image|video|photo) (placeholder|thumbnail)\s*$",
    # --- English: counts / stats / timestamps ---
    r"^\d[\d,.]*[KMB]?\s*(likes?|comments?|views?|posts?|followers?|following|reels?|plays?)\s*$",
    r"^\d[\d,.]*[KMB]?\s+(posts|followers|following)\s*$",
    r"^view all \d+ comments?\s*$",
    r"^\d{1,3}\s*(s|m|h|d|w|mo|y|sec|secs|seconds?|min|mins|minutes?|hr|hrs|hours?|days?|weeks?|months?|years?)\s*(ago)?\s*$",
    r"^[A-Za-z]{3,9}\s+\d{1,2},\s*\d{4}\s*$",     # "January 5, 2026"
    r"^[A-Za-z]{3,9}\s+\d{1,2}\s*$",              # "January 5"
    r"^\d{1,2}\s+[A-Za-z]{3,9}\s*$",              # "5 January"
    r"^(just now|now|today|yesterday)\s*$",
    r"^\s*[·•|]\s*$",
    # --- Instagram profile meta (business accounts) ---
    r"^followed by\b",
    r"^\d+\s*(posts|followers|following)\s*·",
    r"^(posts|followers|following)\s*·\s*",
    # --- Bengali: IG-এর বাংলা UI ---
    r"^\s*(অনুসরণ করুন|অনুসরণ করা হচ্ছে|ফলো|ফলোয়ার|অনুসরণকারী|পছন্দ|মন্তব্য|শেয়ার|সেভ|সেভ করা|রিলস|অন্বেষণ|নোটিফিকেশন|বার্তা|প্রোফাইল|সৃষ্টি করুন|আরও দেখুন|সব দেখুন|অনুবাদ দেখুন|যাচাইকৃত|বন্ধু|সেটিংস|আপনার কার্যকলাপ|লগ আউট|বাতিল|সম্পন্ন)\s*$",
    r"^\s*(বাংলা|ইংরেজি|হিন্দি|স্প্যানিশ|ফরাসি|জার্মান|আরবি|রুশ|জাপানি|কোরিয়ান)\s*$",
]

# Instagram footer-এর language list একটা লম্বা লাইনে জোড়া লেগে থাকে
# ("AfrikaansČeštinaDansk…English…বাংলা")। লাইনে ৪টার বেশি ভাষার নাম পেলে বাদ।
IG_LANG_HITS = re.compile(
    r"(afrikaans|čeština|dansk|deutsch|ελληνικά|english|español|suomi|français|"
    r"magyar|bahasa|italiano|日本語|한국어|nederlands|norsk|polski|português|"
    r"русский|svenska|türkçe|中文|العربية|فارسی|עברית|ไทย|tiếng việt|हिन्दी|বাংলা|"
    r"filipino|melayu|română|українська)",
    re.I,
)

# সবসময় বাদ: pure-URL, separator, emoji-only, pure-number
URL_ONLY = re.compile(r"^\s*(https?://\S+|www\.\S+)\s*$", re.I)
SEPARATOR = re.compile(r"^\s*[-*_=~•·.](\s*[-*_=~•·.]){2,}\s*$")
PURE_NUMBER = re.compile(r"^\s*\d[\d\s,./]*[kKmM]?\s*$")
EMOJI_ONLY = re.compile(
    r"^\s*[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u20E3\s]+\s*$"
)

# Instagram/Facebook image+video CDN URLs. Post media is surfaced by Crawl4AI as
# nested markdown ("[![caption](https://…fbcdn.net/…?stp=dst-jpg…)"); the signed
# URL is often thousands of characters and carries nothing useful for lead-gen.
CDN_BLOB = re.compile(r"(?:fbcdn\.net|cdninstagram\.com)/", re.I)
# A nested/incomplete markdown image fragment ("[![caption" split across lines)
BROKEN_IMAGE = re.compile(r"\[!\[")

# preprocessing-এ ব্যবহৃত
# URL অংশে escaped paren \( \) থাকতে পারে (SVG data-URI), তাই [^)]* নয় —
# (?:[^()\\]|\\.)* দিয়ে escaped sequence-গুলোকে এক ইউনিট ধরা হয়
IMAGE_LINK = re.compile(r"!\[[^\]]*\]\(((?:[^()\\]|\\.)*)\)")
TEXT_LINK = re.compile(r"\[([^\]]*)\]\(((?:[^()\\]|\\.)*)\)")
ENCODED_JUNK = re.compile(r"(?:%[0-9A-Fa-f]{2}){5,}")
COMBINING_JUNK = re.compile(r"[\u034F\u200D\uFE0F\u0300-\u036F]")

# Twitter: শুধু hashtag-এর লাইন (trending sidebar)। _clean_line()-এর
# heading-strip (# বাদ) আগে চেক করতে হয় — নাহলে "#Automation" হয়ে যায়
# "Automation" এবং pattern ম্যাচ করে না।
TW_HASHTAG_ONLY = re.compile(r"^#\S+\s*$")

_COMPILED_STRONG = [re.compile(p, re.I) for p in STRONG_LABELS]
_COMPILED_ALL = [re.compile(p, re.I) for p in ALL_LINE_PATTERNS]
_COMPILED_NOISE = [re.compile(p, re.I) for p in NOISE_PATTERNS]

_COMPILED_TW_STRONG = [re.compile(p, re.I) for p in TWITTER_STRONG_LABELS]
_COMPILED_TW_ALL = [re.compile(p, re.I) for p in TWITTER_ALL_LINE_PATTERNS]
_COMPILED_TW_NOISE = [re.compile(p, re.I) for p in TWITTER_NOISE_PATTERNS]

_COMPILED_IG_STRONG = [re.compile(p, re.I) for p in INSTAGRAM_STRONG_LABELS]
_COMPILED_IG_ALL = [re.compile(p, re.I) for p in INSTAGRAM_ALL_LINE_PATTERNS]
_COMPILED_IG_NOISE = [re.compile(p, re.I) for p in INSTAGRAM_NOISE_PATTERNS]


def _clean_line(line: str):
    """
    একটি লাইন preprocess করে: image link বাদ, [text](url) → text,
    markdown marker ছাঁটা। সব বাদ পড়লে None রিটার্ন করে।
    """
    line = line.strip()
    if not line:
        return None

    # giant image/data-URI ব্লব পুরোপুরি বাদ
    line = IMAGE_LINK.sub("", line)
    if "data:image/" in line or "fbcdn.net/rsrc.php" in line:
        return None
    # Instagram: nested image-markdown fragments + huge signed CDN media URLs
    # (long line + CDN host, or an obviously broken "[![" fragment)
    if BROKEN_IMAGE.search(line):
        return None
    if CDN_BLOB.search(line) and (len(line) > 120 or URL_ONLY.match(line)):
        return None
    # percent-encoded junk (SVG-এর ভাঙা টুকরো) বাদ
    if ENCODED_JUNK.search(line):
        return None

    # [text](url) → শুধু display text (URL-এর গোলমাল দূর হয়)
    line = TEXT_LINK.sub(r"\1", line)

    # markdown marker ছাঁটা: heading, bullet, blockquote, ordered list
    line = re.sub(r"^#{1,6}\s*", "", line)
    line = re.sub(r"^[*\-•]\s+", "", line)
    line = re.sub(r"^>\s*", "", line)
    line = re.sub(r"^\d+\.\s+", "", line)

    # trailing separator (· • |) ও অতিরিক্ত whitespace ছাঁটা
    line = re.sub(r"\s*[·•|]\s*$", "", line)
    line = re.sub(r"\s+", " ", line).strip()

    return line or None


def _is_noise_line(line: str, extra_patterns=None, platform: str = "facebook") -> bool:
    """একটি (preprocess করা) লাইন noise কিনা চেক করে।
    platform="twitter" হলে Twitter/X-এর, "instagram" হলে Instagram-এর pattern
    সেট ব্যবহার হয়; ডিফল্ট "facebook" — আগের আচরণই অপরিবর্তিত থাকে।"""
    if not line:
        return True
    if URL_ONLY.match(line) or SEPARATOR.match(line) or PURE_NUMBER.match(line):
        return True
    if EMOJI_ONLY.match(line):
        return True
    # obfuscated variation-selector junk (FB image-post placeholder-এ থাকে)
    if len(COMBINING_JUNK.findall(line)) > 8:
        return True

    low = line.lower()

    # Instagram footer-এর জোড়া-লাগা language list (৪+ ভাষার নাম = noise)
    if platform == "instagram" and len(IG_LANG_HITS.findall(low)) >= 4:
        return True

    if platform == "twitter":
        strong, allp, noisep = _COMPILED_TW_STRONG, _COMPILED_TW_ALL, _COMPILED_TW_NOISE
    elif platform == "instagram":
        strong, allp, noisep = _COMPILED_IG_STRONG, _COMPILED_IG_ALL, _COMPILED_IG_NOISE
    else:
        strong, allp, noisep = _COMPILED_STRONG, _COMPILED_ALL, _COMPILED_NOISE

    # TIER 1: strong label — সব দৈর্ঘ্যের লাইনে প্রযোজ্য
    for pat in strong:
        if pat.search(low):
            return True

    # TIER 2: medium-strong — যেকোনো দৈর্ঘ্যে
    for pat in allp:
        if pat.search(low):
            return True

    # TIER 3: ছোট লাইনে generic noise প্যাটার্ন
    if len(line) <= SHORT_LINE_MAX_CHARS:
        for pat in noisep:
            if pat.search(low):
                return True

    # user-এর নিজের exclude_patterns — সব দৈর্ঘ্যের লাইনে প্রযোজ্য
    if extra_patterns:
        for pat in extra_patterns:
            if re.search(pat, low, re.I):
                return True

    return False


def clean_markdown(markdown, min_block_chars=10, extra_patterns=None, dedupe=True,
                   platform: str = "facebook"):
    """
    markdown থেকে noise ডেটা ফিল্টার করে dict রিটার্ন করে:

    platform="twitter" দিলে Twitter/X-এর, "instagram" দিলে Instagram-এর pattern
    সেট ব্যবহৃত হয় (ডিফল্ট "facebook" — আগের আচরণ অপরিবর্তিত)।

    {
        "cleaned":        পরিষ্কার করা content (লাইন গুলো \n দিয়ে জোড়া),
        "original_lines": ইনপুটে মোট লাইন,
        "removed_lines":  বাদ পড়া লাইন সংখ্যা,
        "kept_lines":     রাখা লাইন সংখ্যা,
        "original_chars": ইনপুট মোট অক্ষর,
        "cleaned_chars":  আউটপুট মোট অক্ষর,
        "removed_chars":  বাদ পড়া অক্ষর,
        "removed_pct":    বাদ পড়া শতাংশ (int)
    }
    """
    empty = {
        "cleaned": "",
        "original_lines": 0,
        "removed_lines": 0,
        "kept_lines": 0,
        "original_chars": 0,
        "cleaned_chars": 0,
        "removed_chars": 0,
        "removed_pct": 0,
    }
    if not markdown or not str(markdown).strip():
        return empty

    text = str(markdown)
    original_chars = len(text)

    kept = []
    seen = set()
    removed = 0
    original_lines = 0

    for raw in text.split("\n"):
        original_lines += 1
        if platform in ("twitter", "instagram") and TW_HASHTAG_ONLY.match(raw.strip()):
            removed += 1
            continue
        line = _clean_line(raw)
        if line is None:
            removed += 1
            continue
        if len(line) < min_block_chars:
            removed += 1
            continue
        if _is_noise_line(line, extra_patterns, platform):
            removed += 1
            continue
        if dedupe:
            key = line.lower()
            if key in seen:
                removed += 1
                continue
            seen.add(key)
        kept.append(line)

    cleaned = "\n".join(kept)
    cleaned_chars = len(cleaned)
    removed_chars = original_chars - cleaned_chars

    return {
        "cleaned": cleaned,
        "original_lines": original_lines,
        "removed_lines": removed,
        "kept_lines": len(kept),
        "original_chars": original_chars,
        "cleaned_chars": cleaned_chars,
        "removed_chars": removed_chars,
        "removed_pct": round(removed_chars / original_chars * 100) if original_chars else 0,
    }
