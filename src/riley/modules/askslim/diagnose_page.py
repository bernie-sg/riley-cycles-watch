#!/usr/bin/env python3
"""
Diagnostic script to understand why instruments aren't loading.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "askslim"

def diagnose():
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # Visible
            slow_mo=1000
        )

        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )

        page = context.new_page()

        try:
            print("1. Navigating to Futures Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/futures-hub/", wait_until="networkidle")

            print("2. Taking initial screenshot...")
            page.screenshot(path=str(ARTIFACTS_DIR / "diag_1_initial.png"))

            print("3. Waiting 5 seconds...")
            time.sleep(5)

            print("4. Taking screenshot after wait...")
            page.screenshot(path=str(ARTIFACTS_DIR / "diag_2_after_wait.png"))

            print("5. Scrolling down...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            print("6. Taking screenshot after scroll...")
            page.screenshot(path=str(ARTIFACTS_DIR / "diag_3_after_scroll.png"))

            print("7. Scrolling back up...")
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2)

            print("8. Taking final screenshot...")
            page.screenshot(path=str(ARTIFACTS_DIR / "diag_4_back_top.png"))

            # Check for iframes
            print("\n9. Checking for iframes...")
            frames = page.frames
            print(f"   Found {len(frames)} frames")
            for i, frame in enumerate(frames):
                print(f"   Frame {i}: {frame.url}")

            # Try to find any clickable elements
            print("\n10. Looking for clickable elements...")
            buttons = page.query_selector_all("button")
            links = page.query_selector_all("a")
            divs = page.query_selector_all("div[onclick], div[role='button']")

            print(f"   Buttons: {len(buttons)}")
            print(f"   Links: {len(links)}")
            print(f"   Clickable divs: {len(divs)}")

            # Save HTML
            print("\n11. Saving HTML...")
            html_path = ARTIFACTS_DIR / "diag_page.html"
            with open(html_path, 'w') as f:
                f.write(page.content())
            print(f"   Saved: {html_path}")

            # Search for SPX in page text
            print("\n12. Searching for 'SPX' in page...")
            page_text = page.evaluate("document.body.textContent")
            if "SPX" in page_text:
                print("   ✓ Found 'SPX' in page text")
            else:
                print("   ✗ 'SPX' not found in page text")

            # Keep browser open
            print("\n" + "="*70)
            print("Browser is open. Check the page manually.")
            print("Screenshots saved to:", ARTIFACTS_DIR)
            print("Press Ctrl+C when done...")
            print("="*70)

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nClosing...")

        finally:
            context.close()
            browser.close()

if __name__ == "__main__":
    diagnose()
