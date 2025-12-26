#!/usr/bin/env python3
"""
Explore Technical Details tab in Equities modal.
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

def explore_technical_details():
    """Explore Technical Details tab structure."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("EXPLORING: Technical Details Tab (AAPL)")
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
            time.sleep(3)

            # Find iframe
            print("\n🔍 Finding iframe...")
            iframe_element = page.wait_for_selector("iframe.eehub-frame", timeout=15000)
            iframe = iframe_element.content_frame()
            print("✓ Got iframe")
            time.sleep(5)

            # Click AAPL
            print("\n🖱 Clicking AAPL...")
            aapl = iframe.wait_for_selector("text=AAPL", timeout=15000)
            aapl.click()
            time.sleep(2)

            # Find modal
            modal = iframe.wait_for_selector("[class*='Modal']", timeout=5000)
            print("✓ Modal opened")

            # Click Technical Details tab
            print("\n🖱 Switching to Technical Details...")
            tech_tab = iframe.wait_for_selector("text=Technical Details", timeout=5000)
            tech_tab.click()
            time.sleep(2)
            print("✓ Switched to Technical Details")

            # Now explore the structure
            print("\n📋 Technical Details Structure:")

            # Check for accordions again
            accordions = iframe.query_selector_all(".MuiAccordion-root")
            print(f"\n  Accordion sections: {len(accordions)}")

            if accordions:
                for i, acc in enumerate(accordions):
                    # Get summary text (the clickable header)
                    summary = acc.query_selector(".MuiAccordionSummary-root")
                    if summary:
                        summary_text = summary.text_content().strip()
                        print(f"    Section {i+1}: {summary_text}")

                        # Try expanding it
                        if i < 5:  # Only expand first 5 to save time
                            try:
                                print(f"      Expanding...")
                                summary.click()
                                time.sleep(1)

                                # Get details content
                                details = acc.query_selector(".MuiAccordionDetails-root")
                                if details:
                                    details_text = details.text_content()[:200]
                                    print(f"      Content: {details_text}...")

                                # Collapse
                                summary.click()
                                time.sleep(0.5)
                            except Exception as e:
                                print(f"      Error expanding: {e}")

            else:
                print("  No accordion sections found")
                # Get all text content
                tech_content = modal.text_content()
                print(f"\n  All Technical Details content (first 2000 chars):")
                print(tech_content[:2000])

            print("\n" + "="*70)
            print("Keeping browser open for 60 seconds for manual inspection...")
            print("="*70)
            time.sleep(60)

            return True

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    explore_technical_details()
