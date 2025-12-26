#!/usr/bin/env python3
"""
Test enhanced scraper with GC - includes all new fields.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from askslim_scraper import scrape_instrument
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

def test_gc_enhanced():
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("ENHANCED SCRAPER TEST: GC (Gold)")
    print("="*70)
    print("\nExtraction includes:")
    print("  ✓ Cycle dates and lengths")
    print("  ✓ Directional Bias")
    print("  ✓ Weekly Key Levels (Support/Resistance)")
    print("  ✓ Daily Key Levels (Support/Resistance)")
    print("  ✓ Video Analysis URL")
    print("  ✓ Charts")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            print("\nNavigating to Futures Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/futures-hub/", wait_until="networkidle")

            import time
            time.sleep(3)

            print("Finding iframe...")
            iframe_element = page.wait_for_selector("iframe.fuhub-frame", timeout=15000)
            iframe = iframe_element.content_frame()
            print("✓ Got iframe")

            time.sleep(5)

            iframe.wait_for_selector("text=/GC", timeout=15000)
            print("✓ Instruments loaded\n")

            # Scrape GC
            result = scrape_instrument(page, "/GC", iframe)

            if result:
                print("\n" + "="*70)
                print("✅ TEST PASSED")
                print("="*70)
                return True
            else:
                print("\n" + "="*70)
                print("❌ TEST FAILED")
                print("="*70)
                return False

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    success = test_gc_enhanced()
    sys.exit(0 if success else 1)
