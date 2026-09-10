# -*- coding: utf-8 -*-
"""
browser_stealth.py — Shared browser-authenticity (stealth) configuration for
login.py and server.py.

Why this exists
---------------
Playwright-controlled Chromium is detectable as automated in several ways:
  - `navigator.webdriver == true`                    (automation flag)
  - WebGL disabled → null renderer. Crawl4AI's *dedicated* launch path
    hardcodes `--disable-gpu --disable-software-rasterizer`, which anti-bot
    sensors read as headless/automated. Its *persistent* launch path respects
    `enable_stealth` and keeps WebGL alive (SwiftShader on WSLg — which is
    also what a real WSLg browser reports, so no vendor spoof is needed).
  - stale / platform-mismatched User-Agent. Crawl4AI's default says
    Chrome/116 on macOS while the installed engine is Chromium 151 on Linux;
    the UA string, Sec-CH-UA client hints and the real engine version then
    disagree. We pin a real Linux Chrome/151 UA so all three line up.
  - `window.chrome.runtime` missing
  - Playwright's default 1080x600 viewport with no outer/inner delta
  - permissions API reporting automation defaults ("denied" notifications)
  - a brand-new profile on every launch (fresh browser = "new device")

What this module applies (identical for the headed login browser and the
headless crawler, so the fingerprint is consistent):
  * `enable_stealth=True` + `use_persistent_context=True` → WebGL stays
    alive and Crawl4AI applies playwright-stealth to crawl pages.
  * `playwright_stealth.Stealth` defaults patched to stay Linux-consistent:
    platform override = "Linux x86_64" (its stock "Win32" would mismatch our
    Linux UA + Sec-CH-UA-Platform), no webgl vendor spoof (SwiftShader is
    truthful for WSLg), no UA/client-hint evasions (already correct).
  * Real Linux Chrome/151 User-Agent matching the installed Chromium binary.
  * Realistic 1366x768 viewport + matching --window-size window.
  * A defensive init script injected into every context (works even if
    playwright-stealth is missing or a page bypasses the adapter):
    hides navigator.webdriver, restores window.chrome.runtime, fixes
    notifications permission to "default", keeps languages/plugins sane.
"""

import os

# Matches the installed Playwright Chromium binary:
#   ~/.cache/ms-playwright/chromium-1234 -> Chromium 151.0.7922.34
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
)

# Realistic laptop-sized viewport; window-size matches so the
# outer/inner-window delta looks like a real desktop browser.
VIEWPORT_WIDTH = 1366
VIEWPORT_HEIGHT = 768

EXTRA_ARGS = [
    "--window-size=1366,768",
]

# Defensive init script — injected into every context Crawl4AI creates.
# Uses try/except and only patches when needed, so it is idempotent even when
# playwright-stealth already applied the same patches.
INIT_SCRIPT = r"""
(() => {
  try { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); } catch (e) {}
  try {
    if (!window.chrome) { window.chrome = {}; }
    if (!window.chrome.runtime) {
      window.chrome.runtime = { connect: () => {}, sendMessage: () => {}, id: undefined };
    }
  } catch (e) {}
  try { Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] }); } catch (e) {}
  // A real browser reports notifications as "default" until the user is asked.
  try { Object.defineProperty(Notification, 'permission', { get: () => 'default' }); } catch (e) {}
  try {
    const origQuery = navigator.permissions.query.bind(navigator.permissions);
    navigator.permissions.query = (p) =>
      p && p.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : origQuery(p);
  } catch (e) {}
  try {
    if (navigator.plugins.length === 0) {
      const pluginData = [
        ['PDF Viewer', 'internal-pdf-viewer'],
        ['Chrome PDF Viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai'],
        ['Chromium PDF Viewer', 'pdf-viewer'],
        ['WebKit built-in PDF', 'internal-pdf-viewer'],
      ].map(([name, filename]) => ({ name, filename, description: 'Portable Document Format', length: 1 }));
      Object.defineProperty(navigator, 'plugins', { get: () => pluginData });
    }
  } catch (e) {}
})();
"""

# Browser profile directory (persistent, real-browser state across runs).
PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_profiles")

_patched = False


def _patch_stealth_defaults():
    """Make Crawl4AI's playwright-stealth adapter Linux-consistent.

    Crawl4AI instantiates playwright_stealth.Stealth() with stock defaults:
    navigator_platform_override="Win32" (mismatches our Linux UA) and webgl
    vendor spoofing (not needed — SwiftShader is what a real WSLg browser
    reports). Patch the constructor defaults once, before any browser is
    created, so the adapter produces a consistent Linux fingerprint.
    """
    global _patched
    if _patched:
        return
    _patched = True
    try:
        import playwright_stealth.stealth as _ps
    except ImportError:
        return  # playwright-stealth not installed — INIT_SCRIPT still covers the core

    _orig_init = _ps.Stealth.__init__

    def _init(self, *args, **kwargs):
        kwargs.setdefault("navigator_platform_override", "Linux x86_64")
        kwargs.setdefault("webgl_vendor", False)            # keep real SwiftShader renderer
        kwargs.setdefault("navigator_user_agent", False)    # context UA already correct
        kwargs.setdefault("navigator_user_agent_data", False)
        kwargs.setdefault("sec_ch_ua", False)               # Crawl4AI header already correct
        _orig_init(self, *args, **kwargs)

    _ps.Stealth.__init__ = _init


def stealth_kwargs(user_data_dir=None):
    """Keyword arguments to merge into any Crawl4AI BrowserConfig(...) call.

    user_data_dir: persistent profile path. login.py passes a stable
    per-platform profile; server.py passes a stable server profile.
    """
    _patch_stealth_defaults()
    if user_data_dir is None:
        user_data_dir = os.path.join(PROFILES_DIR, "default")
    os.makedirs(user_data_dir, exist_ok=True)
    return {
        "enable_stealth": True,
        "use_persistent_context": True,
        "user_data_dir": user_data_dir,
        "user_agent": USER_AGENT,
        "viewport_width": VIEWPORT_WIDTH,
        "viewport_height": VIEWPORT_HEIGHT,
        "extra_args": list(EXTRA_ARGS),
        "init_scripts": [INIT_SCRIPT],
    }
