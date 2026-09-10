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
See photos, videos and more from hasan_automation
Contact Uploading & Non-Users
By continuing, you agree to Instagram's Terms of Use and Privacy Policy.
Down chevron icon
InstagramLog in
nikeVerified 1w
nike and 2 others
Load more comments
More options
Threads hasan_automation
Reels Reels
Messages Messages
Search Search
Notifications Notifications
New post Create
Settings More
Also from Meta Also from Meta
Instagram recommended
Similar accounts
Original audio
Audio is muted Tags
Turn on Notifications
Know right away when people follow you or like and comment on your photos.
Turn OnNot Now
Sonakshi SinhaVerified
[![No moment is too small to win.
Grab the Sabrina 4 “The Switch” launching 9.5](https://instagram.fdac110-1.fna.fbcdn.net/v/t51.82787-15/791144760_18627521548035900_8030782657832792891_n.jpg?stp=dst-jpg_e15_tt6&_nc_cat=106&ig_cache_key=Mzk3NzM1Mzk4NzIzMzgxNzcxOA%3D%3D.3-ccb7-5)
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
    # real lines observed in a live logged-out crawl of instagram.com/nike (2026-09-10)
    check("see-photos interstitial removed", "See photos, videos and more from" not in cleaned)
    check("contact-uploading link removed", "Contact Uploading" not in cleaned)
    check("consent line removed", "By continuing, you agree" not in cleaned)
    check("icon alt-text removed", "chevron icon" not in cleaned)
    check("concatenated wall header removed", "InstagramLog in" not in cleaned)
    # real lines observed in a live crawl of a public nike post (2026-09-10)
    check("author+badge+time glued line removed", "nikeVerified 1w" not in cleaned)
    check("'and N others' tag row removed", "nike and 2 others" not in cleaned)
    check("load-more-comments removed", "Load more comments" not in cleaned)
    check("'More options' menu removed", "More options" not in cleaned)
    check("Threads CTA line removed", "Threads hasan_automation" not in cleaned)
    # real lines observed in a live AUTHENTICATED crawl (2026-09-10, logged-in feed)
    check("doubled nav labels removed", not any(x in cleaned for x in ("Reels Reels", "Messages Messages", "Search Search", "Notifications Notifications")))
    check("'New post Create' removed", "New post Create" not in cleaned)
    check("'Settings More' removed", "Settings More" not in cleaned)
    check("'Also from Meta' removed", "Also from Meta" not in cleaned)
    check("'Instagram recommended' removed", "Instagram recommended" not in cleaned)
    check("'Similar accounts' removed", "Similar accounts" not in cleaned)
    check("audio chrome removed", "Original audio" not in cleaned and "Audio is muted" not in cleaned)
    check("notification prompts removed", "Turn on Notifications" not in cleaned and "Know right away when people" not in cleaned and "Turn OnNot Now" not in cleaned)
    check("glued badge on a name removed", "Sonakshi SinhaVerified" not in cleaned)
    check("CDN image blob removed", "fbcdn.net" not in cleaned and "stp=dst-jpg" not in cleaned)
    check("broken image-markdown fragment removed", "No moment is too small" not in cleaned)
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
