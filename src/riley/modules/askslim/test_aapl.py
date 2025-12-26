#!/usr/bin/env python3
"""
Test Equities scraper with AAPL.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from askslim_equities_scraper import scrape_equity_instrument
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import time

load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

def test_aapl():
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("EQUITIES SCRAPER TEST: AAPL (Apple)")
    print("="*70)
    print("\nExtraction includes:")
    print("  ✓ Cycle dates and lengths")
    print("  ✓ Directional Bias")
    print("  ✓ Weekly Key Levels (Support/Resistance)")
    print("  ✓ Daily Key Levels (Support/Resistance)")
    print("  ✓ Video Analysis URL (if available)")
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
            print("\n📡 Navigating to Equities/ETFs Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/equities-and-etfs-hub/", wait_until="networkidle")
            time.sleep(3)

            print("🔍 Finding iframe...")
            iframe_element = page.wait_for_selector("iframe.eehub-frame", timeout=15000)
            iframe = iframe_element.content_frame()
            print("✓ Got iframe")

            time.sleep(5)

            iframe.wait_for_selector("text=AAPL", timeout=15000)
            print("✓ Instruments loaded\n")

            # Scrape AAPL
            result = scrape_equity_instrument(page, "AAPL", iframe)

            if result:
                print("\n" + "="*70)
                print("✅ TEST PASSED")
                print("="*70)
                print(f"\n📊 Data Extracted:")
                print(f"  Symbol: {result['askslim_symbol']} → {result['riley_symbol']}")
                print(f"  Weekly: {result['weekly_date']} ({result['weekly_length']} bars)")
                print(f"  Daily:  {result['daily_date']} ({result['daily_length']} bars)")
                print(f"  Directional Bias: {result['directional_bias']}")
                print(f"  Video URL: {result['video_url']}")
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
    success = test_aapl()
    sys.exit(0 if success else 1)
