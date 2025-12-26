#!/usr/bin/env python3
"""
Explore the Equities/ETFs Hub to understand structure.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import time

load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

def explore_equities_hub():
    """Explore the Equities/ETFs Hub structure."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("EXPLORING: Equities/ETFs Hub")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            print("\n📡 Navigating to Equities/ETFs Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/equities-and-etfs-hub/", wait_until="networkidle")

            print("⏳ Waiting for page to load...")
            time.sleep(3)

            # Check for iframe similar to Futures Hub
            print("\n🔍 Checking for iframe...")
            iframes = page.query_selector_all("iframe")
            print(f"  Found {len(iframes)} iframe(s)")

            for i, iframe_elem in enumerate(iframes):
                src = iframe_elem.get_attribute("src")
                class_name = iframe_elem.get_attribute("class")
                print(f"  Iframe {i+1}: class='{class_name}' src='{src}'")

            # Try to find the main iframe (might be similar pattern)
            iframe_element = page.query_selector("iframe.eqhub-frame") or page.query_selector("iframe.fuhub-frame") or iframes[0] if iframes else None

            if not iframe_element:
                print("\n❌ No iframe found - different structure than Futures Hub")
                print("Checking for instruments directly on page...")

                # Check if instruments are directly on the page (not in iframe)
                instrument_links = page.query_selector_all("a, button, div[role='button']")
                print(f"\nFound {len(instrument_links)} potential clickable elements")

                # Look for common ticker patterns
                text_content = page.evaluate("document.body.textContent")
                import re
                tickers = re.findall(r'\b[A-Z]{1,5}\b', text_content)
                unique_tickers = sorted(set(tickers))[:50]  # First 50 unique
                print(f"\nPotential tickers found: {', '.join(unique_tickers)}")

            else:
                print("\n✓ Found iframe")
                iframe = iframe_element.content_frame()
                print("✓ Got iframe content")

                print("\n⏳ Waiting for instruments to load...")
                time.sleep(5)

                # Try to find instruments
                print("\n🔍 Looking for instruments...")

                # Check for text patterns common in stock tickers
                text_elements = iframe.query_selector_all("text=/^[A-Z]{1,5}$/")
                print(f"  Found {len(text_elements)} potential ticker elements")

                # Get all text content to see what's available
                instruments_text = iframe.evaluate("document.body.textContent")

                # Look for common equity symbols
                import re
                tickers = re.findall(r'\b(SPY|QQQ|IWM|DIA|AAPL|MSFT|GOOGL|AMZN|TSLA|NVDA|META)\b', instruments_text)
                unique_tickers = sorted(set(tickers))

                if unique_tickers:
                    print(f"\n✓ Found common tickers: {', '.join(unique_tickers)}")
                else:
                    print("\n⚠ No common tickers found")
                    print("First 500 chars of iframe content:")
                    print(instruments_text[:500])

            print("\n" + "="*70)
            print("Keeping browser open for 30 seconds for manual inspection...")
            print("="*70)
            time.sleep(30)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    explore_equities_hub()
