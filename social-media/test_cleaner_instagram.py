# -*- coding: utf-8 -*-
"""test_cleaner_instagram.py — cleaner.py-র Instagram cleaning ইউনিট টেস্ট
(realistic noisy IG profile markdown fixture সহ; platform="instagram" পথ টেস্ট করে)"""
import sys
sys.path.insert(0, "/home/openclaw/hermesworkspace/social-media")
from cleaner import clean_markdown

FIXTURE = """Instagram
Search
Explore
Reels
Messages
Notifications
Create
Threads
More
Profile
hasan_automation
Verified
Follow
Message
1,234 posts
12.4K followers
890 following
Suman Traders — n8n ও OpenClaw দিয়ে বিজনেস অটোমেশন সেটআপ করি। ডেইলি ২০+ ম্যানুয়াল অর্ডার প্রসেস অটোমেট করে দিই, ইনবক্সে ডিটেইলস।
Dhaka, Bangladesh
www.automationbyhasan.com
Followed by rahim_ahmed and 12 others
Highlight
Story 1
Story 2
Suggested for you
daily_deals_dhaka
Follow
Liked by karim_uddin and 45 others
karim_uddin: ভাই আপনার অটোমেশন সার্ভিসের দাম কত? আমার ফেসবুক পেজে প্রতিদিন অর্ডার ম্যানেজ করতে পারব?
View all 12 comments
2 hours ago
Log in to like or comment
Add a comment
Post
About Blog Jobs Help API Privacy Terms Locations Instagram Lite Threads
AfrikaansČeštinaDanskDeutschΕλληνικάEnglishEnglish (UK)EspañolSuomiFrançaisMagyarBahasa IndonesiaItaliano日本語한국어NederlandsNorskPolskiPortuguêsРусскийSvenskaTürkçe中文العربيةفارسیעבריתไทยTiếng Việtहिन्दीবাংলা
© 2026 Instagram from Meta
More posts from hasan_automation
ফলো করুন
শেয়ার
সেভ
আরও দেখুন
নোটিফিকেশন
"""


def main():
    res = clean_markdown(FIXTURE, platform="instagram")
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

    check("Bengali bio/caption kept", "n8n" in cleaned and "বিজনেস অটোমেশন" in cleaned)
    check("real comment kept", "আপনার অটোমেশন সার্ভিসের দাম কত" in cleaned)
    check("username kept", "hasan_automation" in cleaned)
    check("location line kept", "Dhaka, Bangladesh" in cleaned)
    check("nav removed (Explore/Reels/Messages)", "Explore" not in cleaned and "Reels" not in cleaned and "Messages" not in cleaned)
    check("nav removed (Notifications/Threads)", "Notifications" not in cleaned and "Threads" not in cleaned)
    check("follow button removed", "Follow" not in cleaned and "Message" not in cleaned)
    check("verified badge removed", "Verified" not in cleaned)
    check("stats removed", "1,234 posts" not in cleaned and "12.4K followers" not in cleaned and "890 following" not in cleaned)
    check("comments chrome removed", "View all 12 comments" not in cleaned and "Add a comment" not in cleaned)
    check("likes line removed", "Liked by karim_uddin" not in cleaned)
    check("timestamp removed", "2 hours ago" not in cleaned)
    check("login wall removed", "Log in to like or comment" not in cleaned)
    check("suggestions label removed", "Suggested for you" not in cleaned)
    check("followed-by meta removed", "Followed by rahim_ahmed" not in cleaned)
    check("pure-URL line removed", "www.automationbyhasan.com" not in cleaned)
    check("highlight/story chrome removed", "Highlight" not in cleaned and "Story 1" not in cleaned)
    check("footer language blob removed", "Afrikaans" not in cleaned and "Čeština" not in cleaned)
    check("footer copyright removed", "Instagram from Meta" not in cleaned)
    check("footer links removed", "Instagram Lite" not in cleaned and "API" not in cleaned)
    check("more-posts block removed", "More posts from" not in cleaned)
    check("bengali UI removed", "ফলো করুন" not in cleaned and "সেভ" not in cleaned and "আরও দেখুন" not in cleaned)
    # kept: username, bio/caption, location, suggested-handle line, real comment
    check("kept_lines == 5", res["kept_lines"] == 5)
    check("removed_lines > 0", res["removed_lines"] > 0)
    check("removed_pct > 50", res["removed_pct"] > 50)

    print()
    ok = all(results)
    print("ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
