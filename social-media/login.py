#!/usr/bin/env python3
"""
login.py — Manual social-media login session saver for Crawl4AI.

Opens a visible (headed) Chromium browser, lets you log in by hand, then saves
the authenticated session (cookies + localStorage) to a state file, which
server.py loads via BrowserConfig(storage_state=...).

Supported platforms:
    facebook (default) -> https://www.facebook.com/  -> fb_state.json
    twitter            -> https://x.com/             -> twitter_state.json

The browser NEVER closes by itself — it stays open until you press Enter in the
terminal (or Ctrl+C). When a successful login is detected (or you press Enter),
the current session is saved to the platform's state file.

Usage:
    python login.py                    # Facebook (default)
    python login.py --platform twitter # Twitter / X
"""

import argparse
import asyncio
import json
import os
import queue
import signal
import sys
import threading
import time

# Show progress messages in real time even when stdout is redirected
# (default block-buffering would hide them until the script exits).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# ---------------------------------------------------------------------------
# FIX 1 (root cause): headed browsers die instantly when DISPLAY is missing.
#   WSLg provides an X server at /tmp/.X11-unix/X0 (display ":0"), but the
#   DISPLAY env var is not always exported (e.g. when launched from an
#   automated or non-interactive shell). Detect and set it before Chromium.
# ---------------------------------------------------------------------------
def ensure_display() -> None:
    if os.environ.get("DISPLAY"):
        return
    for i in range(10):
        if os.path.exists(f"/tmp/.X11-unix/X{i}"):
            os.environ["DISPLAY"] = f":{i}"
            print(f"[login] DISPLAY was not set - using X server ':{i}' (WSLg).")
            return
    print("[login] ERROR: no X server found (DISPLAY unset, no /tmp/.X11-unix/X*).")
    print("        A headed browser needs a display. If this is WSL, make sure WSLg")
    print("        is enabled (Windows 11 with WSL 2; reopen the terminal after enabling).")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Platform configuration. `--platform` chooses which one to log into:
#   facebook (default) -> fb_state.json, login detected via the c_user cookie
#   twitter            -> twitter_state.json, login detected via auth_token
# ---------------------------------------------------------------------------
PLATFORMS = {
    "facebook": {
        "name": "Facebook",
        "url": "https://www.facebook.com/",
        "state_file": "fb_state.json",
        "login_cookie": "c_user",  # set only after a successful Facebook login
    },
    "twitter": {
        "name": "Twitter (X)",
        "url": "https://x.com/",
        "state_file": "twitter_state.json",
        "login_cookie": "auth_token",  # X sets this only after a successful login
    },
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Manual social-media login session saver (Facebook or Twitter/X)."
    )
    parser.add_argument(
        "--platform",
        choices=sorted(PLATFORMS),
        default="facebook",
        help="Which platform to log into (default: facebook)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Graceful Ctrl+C handling.
#   Letting KeyboardInterrupt rip through asyncio mid-Playwright-call wedges
#   the browser protocol and hangs shutdown. Instead a signal handler only
#   sets a flag; every loop checks it, and the `finally` block closes the
#   browser from a normal (never-cancelled) task. Second Ctrl+C force-quits.
# ---------------------------------------------------------------------------
SHUTDOWN = {"requested": False, "force": False}


def install_sigint_handler(loop) -> None:
    def _on_sigint() -> None:
        if SHUTDOWN["requested"]:
            SHUTDOWN["force"] = True
            print("[login] Force quitting...")
            os._exit(1)
        SHUTDOWN["requested"] = True
        print("[login] Ctrl+C received - closing the browser...")

    try:
        loop.add_signal_handler(signal.SIGINT, _on_sigint)
    except (NotImplementedError, RuntimeError):
        pass  # fall back to the default KeyboardInterrupt behavior


# ---------------------------------------------------------------------------
# Non-blocking stdin reader: a single background DAEMON thread pushes every
# pressed line into a queue, so the async loop can poll "did the user press
# Enter?" without blocking the browser event loop. Daemon = never blocks
# process exit (Ctrl+C / SIGINT shuts down cleanly).
# ---------------------------------------------------------------------------
def _stdin_reader(q: "queue.Queue") -> None:
    while True:
        line = sys.stdin.readline()
        if line:            # real input (Enter) -> queue it
            q.put(line)
        else:               # EOF (stdin closed) -> don't busy-loop, don't fake a press
            time.sleep(0.1)


async def wait_for_enter(stdin_q: "queue.Queue") -> None:
    """Block until the user presses Enter or Ctrl+C (queue poll, no threads)."""
    while not SHUTDOWN["requested"]:
        try:
            stdin_q.get_nowait()
            return
        except queue.Empty:
            await asyncio.sleep(0.2)


async def main() -> None:
    ensure_display()
    install_sigint_handler(asyncio.get_running_loop())

    platform_name = parse_args().platform
    cfg = PLATFORMS[platform_name]
    print(f"[login] Platform: {cfg['name']} (session -> {cfg['state_file']})")

    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from browser_stealth import stealth_kwargs, PROFILES_DIR
    import os

    # persistent per-platform profile: the browser keeps real history/cache
    # between runs instead of looking like a brand-new device every time
    profile_dir = os.path.join(PROFILES_DIR, platform_name)
    # visible GUI + stealth (real UA, WebGL alive, webdriver hidden, etc.)
    browser_config = BrowserConfig(headless=False, verbose=False,
                                   **stealth_kwargs(user_data_dir=profile_dir))
    run_config = CrawlerRunConfig(session_id=f"{cfg['state_file']}-login", verbose=False)

    crawler = AsyncWebCrawler(config=browser_config)

    stdin_q: "queue.Queue" = queue.Queue()
    threading.Thread(target=_stdin_reader, args=(stdin_q,), daemon=True).start()

    def enter_pressed() -> bool:
        try:
            stdin_q.get_nowait()
            return True
        except queue.Empty:
            return False

    try:
        await crawler.start()

        # FIX 2: use Crawl4AI 0.9.x's browser-manager API to get a LIVE
        # (page, context) pair. `arun()` is a full crawl cycle that tears the
        # page down afterwards - useless for manual login. `get_storage_state()`
        # does not exist in 0.9.2 (the old export path is broken too); the
        # reliable way is Playwright's context.storage_state().
        page, context = await crawler.crawler_strategy.browser_manager.get_page(run_config)

        try:
            await page.goto(cfg["url"], wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"[login] Warning: could not load {cfg['url']} ({e}).")
            print("        You can type the address manually in the browser.")

        print("=" * 62)
        print(f"[login] Browser is open. Log in to {cfg['name']} in the window now.")
        print("[login] The browser will stay open - there is NO time limit.")
        print("[login] When you are logged in, the session is saved automatically.")
        print("[login] (Pressing Enter here also saves the session.)")
        print("=" * 62)

        ever_logged_in = False
        while not SHUTDOWN["requested"]:
            # Wait until either: login detected, Enter pressed, or Ctrl+C
            logged_in = False
            while not enter_pressed() and not SHUTDOWN["requested"]:
                cookies = await context.cookies()
                if any(c.get("name") == cfg["login_cookie"] for c in cookies):
                    logged_in = True
                    break
                await asyncio.sleep(2)

            if SHUTDOWN["requested"]:
                break

            if logged_in:
                ever_logged_in = True
                print(f"[login] {cfg['name']} login detected (cookie '{cfg['login_cookie']}' found).")

            # Save whatever session state we have right now
            state = await context.storage_state()
            with open(cfg["state_file"], "w") as f:
                json.dump(state, f, indent=2)
            n_cookies = len(state.get("cookies", []))
            print(f"[login] Session saved -> {cfg['state_file']} ({n_cookies} cookies).")

            if ever_logged_in:
                # Logged in + saved: keep the browser open until the user
                # explicitly closes it by pressing Enter (or Ctrl+C).
                print("[login] Login complete. The browser stays open - press Enter")
                print("        in the terminal to close it when you are done.")
                await wait_for_enter(stdin_q)
                break

            print(f"[login] No login detected yet (no '{cfg['login_cookie']}' cookie).")
            print("        Keep logging in - the browser stays open. Press Enter")
            print("        to save the session again once you are logged in.")

        # Ctrl+C while logged in: capture the session before closing
        if SHUTDOWN["requested"] and ever_logged_in:
            try:
                state = await context.storage_state()
                with open(cfg["state_file"], "w") as f:
                    json.dump(state, f, indent=2)
                n_cookies = len(state.get("cookies", []))
                print(f"[login] Session saved -> {cfg['state_file']} ({n_cookies} cookies).")
            except Exception:
                pass

    finally:
        try:
            await crawler.close()
        except Exception:
            pass
        print("[login] Browser closed. Goodbye.")


if __name__ == "__main__":
    asyncio.run(main())
