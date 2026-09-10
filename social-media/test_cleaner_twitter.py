# -*- coding: utf-8 -*-
"""test_cleaner_twitter.py — cleaner.py-র Twitter/X cleaning ইউনিট টেস্ট
(realistic noisy X markdown fixture সহ; platform="twitter" পথ টেস্ট করে)"""
import sys
sys.path.insert(0, "/home/openclaw/hermesworkspace/social-media")
from cleaner import clean_markdown

FIXTURE = """For you
Following
Explore
Notifications
Messages
·
Home
Elon Musk @elonmusk · 2h
Excited to share that our automation startup just crossed 10,000 customers. This is a long real tweet about AI automation services and how businesses save time with n8n workflows.
1.2K
345
89
Reply
Repost
Like
View
Bookmark
Share
Replying to @elonmusk
Great milestone Elon! We use automation daily and it saves us hours. This is another real reply that should be kept because it is genuine user content.
12
3
· 5h
Show more
Promoted
Who to follow
Trending now
What's happening
#Automation
2,345 replies
New to X?
Sign up now
Already have an account? Log in
Sign in to X
Joined March 2021
Jan 5, 2026
1,234
12.4K
Following
Followers
আমার নতুন অটোমেশন সার্ভিস চালু করলাম! n8n দিয়ে কাস্টমার সাপোর্ট অটোমেশন করে দিচ্ছি। যে কেউ ইন্টারেস্টেড হলে ইনবক্স করুন। এটি একটি রিয়েল টুইটের মতো দীর্ঘ টেক্সট যা রাখা উচিত।
@hasan_automation · 1d
উত্তর দিন
রিপোস্ট
লাইক
দেখুন
বুকমার্ক
শেয়ার
আরও দেখুন
·
Conversation
View quotes
Post your reply
Everyone can reply
Relevant people
Politics · Trending
To view keyboard shortcuts, press question mark
HomeExploreNotificationsFollowChatGrokBookmarksCreator StudioPremiumProfile
"""


def main():
    res = clean_markdown(FIXTURE, platform="twitter")
    cleaned = res["cleaned"]

    print("=== STATS ===")
    for k, v in res.items():
        print(f"  {k}: {v}")
    print()
    print("=== CLEANED OUTPUT ===")
    print(cleaned)
    print("======================")

    # --- assertions ---
    results = []
    def check(name, cond):
        results.append(cond)
        print(f"[{'PASS' if cond else 'FAIL'}] {name}")

    check("English tweet kept", "10,000 customers" in cleaned)
    check("reply kept", "Great milestone Elon" in cleaned)
    check("Bengali tweet kept (n8n)", "n8n" in cleaned)
    check("author line kept (elon)", "@elonmusk · 2h" in cleaned)
    check("author line kept (hasan)", "@hasan_automation · 1d" in cleaned)
    check("nav removed (Explore)", "Explore" not in cleaned)
    check("nav removed (Notifications)", "Notifications" not in cleaned)
    check("nav removed (For you)", "For you" not in cleaned)
    check("action bar removed", "Repost" not in cleaned and "Bookmark" not in cleaned and "Share" not in cleaned)
    check("reply chrome removed", "Replying to @elonmusk" not in cleaned)
    check("counts removed", "1.2K" not in cleaned and "2,345 replies" not in cleaned)
    check("timestamp removed", "· 5h" not in cleaned and "Jan 5, 2026" not in cleaned)
    check("promoted label removed", "Promoted" not in cleaned)
    check("trends removed", "Trending now" not in cleaned and "What's happening" not in cleaned)
    check("sidebar removed", "Who to follow" not in cleaned)
    check("hashtag-only removed", "#Automation" not in cleaned)
    check("login wall removed", "New to X?" not in cleaned and "Sign up now" not in cleaned)
    check("sign-in prompt removed", "Sign in to X" not in cleaned and "Already have an account" not in cleaned)
    check("profile meta removed", "Joined March 2021" not in cleaned)
    check("profile stats removed", "1,234" not in cleaned and "12.4K" not in cleaned)
    check("follow labels removed", "Following" not in cleaned and "Followers" not in cleaned)
    check("show more removed", "Show more" not in cleaned)
    check("bengali UI removed", "উত্তর দিন" not in cleaned and "রিপোস্ট" not in cleaned and "আরও দেখুন" not in cleaned)
    check("status chrome removed", "Conversation" not in cleaned and "View quotes" not in cleaned)
    check("reply box removed", "Post your reply" not in cleaned and "Everyone can reply" not in cleaned)
    check("sidebar removed (relevant/trending)", "Relevant people" not in cleaned and "· Trending" not in cleaned)
    check("keyboard shortcut hint removed", "keyboard shortcuts" not in cleaned)
    check("concatenated nav removed", "HomeExplore" not in cleaned and "Creator StudioPremiumProfile" not in cleaned)
    check("kept_lines == 5", res["kept_lines"] == 5)
    check("removed_lines > 0", res["removed_lines"] > 0)
    check("removed_pct > 30", res["removed_pct"] > 30)

    print()
    ok = all(results)
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
