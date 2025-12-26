#!/usr/bin/env python3
"""
Test scraper on just SPX to verify everything works.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from askslim_scraper import run_scraper, ASKSLIM_TO_RILEY, scrape_instrument
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
ASKSLIM_HEADLESS = os.getenv("ASKSLIM_HEADLESS", "false").lower() == "true"

DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

def test_spx_only():
    """Test scraping just SPX."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("TEST: Scraping SPX only")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # Force visible browser for testing
            slow_mo=500
        )
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            # Navigate to Futures Hub
            print("\nNavigating to Futures Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/futures-hub/", wait_until="networkidle")

            # Wait for page to load
            print("Waiting for page to load...")
            import time
            time.sleep(3)

            # Find the futures hub iframe
            print("Looking for futures hub iframe...")
            iframe_element = page.wait_for_selector("iframe.fuhub-frame", timeout=15000)
            print("✓ Found iframe")

            # Get the iframe's content frame
            iframe = iframe_element.content_frame()
            print("✓ Got iframe content")

            # Wait for instruments to load inside iframe
            print("Waiting for instruments to load in iframe...")
            time.sleep(5)

            # Wait for SPX to be visible inside iframe
            print("Waiting for SPX to appear in iframe...")
            iframe.wait_for_selector("text=SPX", timeout=15000)
            print("✓ SPX is visible in iframe")

            # Scrape SPX
            result = scrape_instrument(page, "SPX", iframe)

            if result:
                print("\n" + "="*70)
                print("TEST PASSED")
                print("="*70)
                print(f"SPX → ES")
                print(f"Weekly: {result['weekly_date']} ({result['weekly_length']} bars)")
                print(f"Daily: {result['daily_date']} ({result['daily_length']} bars)")
                return True
            else:
                print("\n" + "="*70)
                print("TEST FAILED")
                print("="*70)
                return False

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    success = test_spx_only()
    sys.exit(0 if success else 1)
