#!/usr/bin/env python3
"""
Explore clicking an equity instrument to see modal structure.
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

def explore_equity_modal():
    """Click on an equity to see modal structure."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("EXPLORING: Equity Instrument Modal (AAPL)")
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

            # Find the iframe
            print("\n🔍 Finding iframe...")
            iframe_element = page.wait_for_selector("iframe.eehub-frame", timeout=15000)
            iframe = iframe_element.content_frame()
            print("✓ Got iframe")

            time.sleep(5)

            # Try to click on AAPL
            print("\n🔍 Looking for AAPL...")

            # Try different selectors
            aapl_selectors = [
                "text=/^AAPL$/",
                "text=AAPL",
                "text=Apple",
                "[data-symbol='AAPL']",
                "div:has-text('AAPL')",
            ]

            aapl_element = None
            for selector in aapl_selectors:
                try:
                    aapl_element = iframe.wait_for_selector(selector, timeout=3000)
                    if aapl_element:
                        print(f"✓ Found AAPL using selector: {selector}")
                        break
                except Exception as e:
                    print(f"  ✗ Selector '{selector}' failed: {e}")

            if not aapl_element:
                print("❌ Could not find AAPL element")
                print("\nGetting all visible text to help identify structure...")
                all_text = iframe.evaluate("document.body.innerText")
                print(all_text[:1000])
                return False

            print("\n🖱 Clicking AAPL...")
            aapl_element.click()
            time.sleep(2)

            # Check for modal
            print("\n🔍 Checking for modal...")
            modal_selectors = [
                "[role='dialog']",
                ".MuiDialog-root",
                ".modal",
                "[class*='Modal']",
            ]

            modal = None
            for selector in modal_selectors:
                try:
                    modal = iframe.wait_for_selector(selector, timeout=3000)
                    if modal:
                        print(f"✓ Found modal using selector: {selector}")
                        break
                except:
                    pass

            if not modal:
                print("❌ No modal found")
                return False

            # Check modal structure
            print("\n📋 Modal Structure:")

            # Check for tabs
            tabs = iframe.query_selector_all("[role='tab'], .MuiTab-root")
            print(f"  Tabs: {len(tabs)}")
            for i, tab in enumerate(tabs[:10]):  # First 10 tabs
                tab_text = tab.text_content()
                print(f"    Tab {i+1}: {tab_text}")

            # Check for accordion sections
            accordions = iframe.query_selector_all(".MuiAccordion-root, [class*='Accordion']")
            print(f"\n  Accordion sections: {len(accordions)}")
            for i, acc in enumerate(accordions[:10]):  # First 10
                acc_text = acc.text_content()[:100]  # First 100 chars
                print(f"    Section {i+1}: {acc_text}...")

            # Get modal content
            modal_text = modal.text_content()
            print(f"\n  Modal content (first 1000 chars):")
            print(modal_text[:1000])

            print("\n" + "="*70)
            print("Keeping browser open for 60 seconds for manual inspection...")
            print("="*70)
            time.sleep(60)

            return True

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    explore_equity_modal()
