#!/usr/bin/env python3
"""
Explore SPX instrument page structure to understand:
1. How to access Technical Details
2. Where cycle data is located
3. Where chart images are
4. How to download charts
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

# Load environment variables
load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
ASKSLIM_HEADLESS = os.getenv("ASKSLIM_HEADLESS", "false").lower() == "true"

DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv(
    "ASKSLIM_STORAGE_STATE_PATH",
    str(DEFAULT_STORAGE_STATE_PATH)
)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "askslim"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def explore_spx():
    """Explore SPX instrument structure."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        raise FileNotFoundError("Run askslim_login.py first")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=ASKSLIM_HEADLESS, slow_mo=500)
        context = browser.new_context(storage_state=str(storage_state_path))
        page = context.new_page()

        try:
            print("Navigating to Futures Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/futures-hub/", wait_until="networkidle")

            # Wait for dynamic content
            print("Waiting for page to fully load...")
            page.wait_for_timeout(3000)

            # Scroll to make sure everything is visible
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1000)
            page.evaluate("window.scrollTo(0, 0)")

            # Take screenshot after load
            page.screenshot(path=str(ARTIFACTS_DIR / "futures_hub_loaded.png"))

            # Save HTML after JavaScript execution
            html_after = ARTIFACTS_DIR / "futures_hub_after_js.html"
            with open(html_after, 'w') as f:
                f.write(page.content())
            print(f"HTML after JS: {html_after}")

            print("\nLooking for SPX button...")
            # Try to find and click SPX
            spx_button = None
            selectors = [
                "text=SPX",
                "button:has-text('SPX')",
                "a:has-text('SPX')",
                "[data-symbol='SPX']",
                "div:has-text('SPX')"
            ]

            for selector in selectors:
                try:
                    spx_button = page.wait_for_selector(selector, timeout=3000)
                    if spx_button:
                        print(f"Found SPX with selector: {selector}")
                        break
                except:
                    pass

            if not spx_button:
                print("ERROR: Could not find SPX button")
                page.screenshot(path=str(ARTIFACTS_DIR / "spx_notfound.png"))
                return

            print("Clicking SPX...")
            spx_button.click()
            page.wait_for_timeout(2000)  # Wait for content to load

            print(f"Current URL: {page.url}")

            # Screenshot after clicking
            page.screenshot(path=str(ARTIFACTS_DIR / "spx_clicked.png"))
            print(f"Screenshot: {ARTIFACTS_DIR / 'spx_clicked.png'}")

            # Look for Technical Details section
            print("\nSearching for 'Technical Details'...")
            tech_details = page.query_selector_all("text=Technical Details")
            print(f"Found {len(tech_details)} elements with 'Technical Details'")

            # Look for Cycle Low Dates
            print("\nSearching for 'Cycle Low Dates'...")
            cycle_dates = page.query_selector_all("text=Cycle Low Dates")
            print(f"Found {len(cycle_dates)} elements with 'Cycle Low Dates'")

            # Look for Cycle Counts
            print("\nSearching for 'Cycle Counts' or 'Dominant Cycle'...")
            cycle_counts = page.query_selector_all("text=/Cycle Counts|Dominant Cycle/i")
            print(f"Found {len(cycle_counts)} elements")

            # Look for Weekly/Daily sections
            print("\nSearching for Weekly/Daily sections...")
            weekly = page.query_selector_all("text=/Weekly/i")
            daily = page.query_selector_all("text=/Daily/i")
            print(f"Found {len(weekly)} 'Weekly' elements")
            print(f"Found {len(daily)} 'Daily' elements")

            # Look for images
            print("\nSearching for images...")
            images = page.query_selector_all("img")
            print(f"Found {len(images)} img elements")

            # Print first few image sources
            for i, img in enumerate(images[:10]):
                src = img.get_attribute("src")
                alt = img.get_attribute("alt")
                print(f"  Image {i+1}: alt='{alt}', src='{src[:80] if src else 'None'}...'")

            # Save HTML
            html_path = ARTIFACTS_DIR / "spx_page.html"
            with open(html_path, 'w') as f:
                f.write(page.content())
            print(f"\nHTML saved: {html_path}")

            # Keep browser open for manual inspection if not headless
            if not ASKSLIM_HEADLESS:
                print("\n" + "="*60)
                print("Browser is open for manual inspection")
                print("Press Ctrl+C when done exploring")
                print("="*60)
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nClosing browser...")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    try:
        explore_spx()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
