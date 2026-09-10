# -*- coding: utf-8 -*-
"""test_cleaner.py — cleaner.py-র ইউনিট টেস্ট (realistic noisy FB markdown fixture সহ)"""
import sys
sys.path.insert(0, "/home/openclaw/hermesworkspace/social-media")
from cleaner import clean_markdown

FIXTURE = """[](https://www.facebook.com/)
  * [](https://www.facebook.com/friends/)
  * [](https://www.facebook.com/groups/)
[Find friends](https://www.facebook.com/friends/)
Number of unread notifications
1
# Notifications
All
Unread
## New
[See all](https://www.facebook.com/notifications/)
[ UnreadWe noticed a new login from a device or location that you don't usually use. Please review. 43m ](https://www.facebook.com/login_alerts/start/?long)
[ UnreadYour business is ready. Create an ad today to help find new customers. 5w ](https://www.facebook.com/?notif)
[ UnreadYour full control of **MR BAD LUCK** was removed. 3w ](https://www.facebook.com/?notif)
### Feed posts
> F
Some Real Post text in English about automation tools and how they help businesses save time. This is a long paragraph with actual content worth keeping for lead generation purposes.
5.2K
270
13
Like
Comment
Share
স্পনসরড
আমার নতুন অটোমেশন সার্ভিস চালু করলাম! n8n দিয়ে কাস্টমার সাপোর্ট অটোমেশন করে দিচ্ছি। যে কেউ ইন্টারেস্টেড হলে ইনবক্স করুন। এটি একটি রিয়েল পোস্টের মতো দীর্ঘ টেক্সট যা রাখা উচিত।
People you may know
https://www.facebook.com/xyz
2 h
Write a comment...
See more
আমার নতুন অটোমেশন সার্ভিস চালু করলাম! n8n দিয়ে কাস্টমার সাপোর্ট অটোমেশন করে দিচ্ছি। যে কেউ ইন্টারেস্টেড হলে ইনবক্স করুন। এটি একটি রিয়েল পোস্টের মতো দীর্ঘ টেক্সট যা রাখা উচিত।
Log in to Facebook
🍕🍔🍟
- - -
42
![](data:image/svg+xml,%3Csvg%20fill='none'%20viewBox='0%200%2016%2016'%3E%3C/svg%3E)
[Privacy](https://www.facebook.com/privacy/policy/) ·
[Terms](https://www.facebook.com/policies?ref=pf) ·
[Ad choices ](https://www.facebook.com/help/568137493302217) ·
[Cookies](https://www.facebook.com/policies/cookies/) ·
More
"""


def main():
    res = clean_markdown(FIXTURE)
    cleaned = res["cleaned"]

    print("=== STATS ===")
    for k, v in res.items():
        print(f"  {k}: {v}")
    print()
    print("=== CLEANED OUTPUT ===")
    print(cleaned)
    print("======================")

    # --- assertions ---
    ok = True
    def check(name, cond):
        global ok
        status = "PASS" if cond else "FAIL"
        if not cond:
            ok = False
        print(f"[{status}] {name}")

    check("English post kept", "Some Real Post" in cleaned)
    check("Bengali post kept (n8n)", "n8n" in cleaned)
    check("duplicate post removed", cleaned.count("n8n") == 1)
    check("empty-link lines removed", "[](" not in cleaned)
    check("nav removed (Marketplace)", "Marketplace" not in cleaned)
    check("Find friends removed", "Find friends" not in cleaned)
    check("suggestion noise removed", "Suggested for you" not in cleaned)
    check("sponsored removed", "স্পনসরড" not in cleaned)
    check("URL-only line removed", "https://www.facebook.com/xyz" not in cleaned)
    check("action bar removed", "Share" not in cleaned and "Comment" not in cleaned and "Like" not in cleaned)
    check("reaction counts removed", "5.2K" not in cleaned and "270" not in cleaned and "13" not in cleaned)
    check("login alert removed", "We noticed a new login" not in cleaned)
    check("ad promo removed", "Create an ad today" not in cleaned)
    check("admin removal notif removed", "MR BAD LUCK" not in cleaned)
    check("heading removed (Notifications)", "# Notifications" not in cleaned and "Feed posts" not in cleaned)
    check("composer placeholder removed", "mind, HT" not in cleaned)
    check("image blob removed", "data:image" not in cleaned)
    check("privacy/terms/cookies removed", "Privacy" not in cleaned and "Terms" not in cleaned and "Cookies" not in cleaned)
    check("time-ago removed", "2 h" not in cleaned)
    check("'See more' removed", "See more" not in cleaned)
    check("login prompt removed", "Log in to Facebook" not in cleaned)
    check("emoji-only removed", "🍕" not in cleaned)
    check("separator removed", "- - -" not in cleaned)
    check("pure number removed", "42" not in cleaned)
    check("kept_lines == 2", res["kept_lines"] == 2)
    check("removed_lines > 0", res["removed_lines"] > 0)
    check("removed_pct > 50", res["removed_pct"] > 50)

    print()
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
