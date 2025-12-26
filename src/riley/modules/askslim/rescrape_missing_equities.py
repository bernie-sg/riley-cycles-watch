#!/usr/bin/env python3
"""
Re-scrape only the missing equity instruments that failed due to scrolling issues.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from askslim_equities_scraper import scrape_equity_instrument, ASKSLIM_BASE_URL, ASKSLIM_STORAGE_STATE_PATH, human_delay
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv

load_dotenv()

ASKSLIM_HEADLESS = os.getenv("ASKSLIM_HEADLESS", "true").lower() == "true"

# Only the instruments that failed due to scrolling
MISSING_INSTRUMENTS = [
    "BABA",   # Alibaba
    "CAT",    # Caterpillar
    "COST",   # Costco
    "DE",     # Deere
    "DIS",    # Disney
    "MCD",    # McDonald's
    "META",   # Meta Platforms
    "NVDA",   # NVIDIA
    "PEP",    # PepsiCo
    "TOL",    # Toll Brothers
    "UBER",   # Uber
    "V",      # Visa
    "WYNN",   # Wynn Resorts
    "XLE",    # Energy ETF
]

def rescrape_missing():
    """Re-scrape only the missing instruments."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("RE-SCRAPING MISSING EQUITIES/ETFs (with scrolling fix)")
    print("="*70)
    print(f"\nInstruments to scrape: {len(MISSING_INSTRUMENTS)}")
    for sym in MISSING_INSTRUMENTS:
        print(f"  • {sym}")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=ASKSLIM_HEADLESS, slow_mo=500)
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            # Navigate to Equities/ETFs Hub
            print("\n📡 Navigating to Equities/ETFs Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/equities-and-etfs-hub/", wait_until="networkidle")
            human_delay(2, 3)

            # Find the eehub iframe
            print("🔍 Looking for eehub iframe...")
            iframe_element = page.wait_for_selector("iframe.eehub-frame", timeout=15000)
            print("✓ Found iframe")

            # Get the iframe's content frame
            iframe = iframe_element.content_frame()
            print("✓ Got iframe content")

            # Wait for instruments to load
            print("⏳ Waiting for instruments to load...")
            human_delay(3, 5)

            # Verify instruments are visible
            iframe.wait_for_selector("text=AAPL", timeout=15000)
            print("✓ Instruments loaded")

            # Scrape missing instruments
            results = []
            for askslim_symbol in MISSING_INSTRUMENTS:
                result = scrape_equity_instrument(page, askslim_symbol, iframe)
                if result:
                    results.append(result)

                # Random delay between instruments (4-8 seconds to avoid bot detection)
                human_delay(4, 8)

            # Summary
            print("\n" + "="*70)
            print("RE-SCRAPING COMPLETE")
            print("="*70)
            print(f"✅ Successfully scraped: {len(results)}/{len(MISSING_INSTRUMENTS)} instruments")

            if len(results) < len(MISSING_INSTRUMENTS):
                failed = set(MISSING_INSTRUMENTS) - {r['askslim_symbol'] for r in results}
                print(f"\n❌ Still failed: {len(failed)}")
                for sym in sorted(failed):
                    print(f"  • {sym}")

            return True

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    success = rescrape_missing()
    sys.exit(0 if success else 1)
