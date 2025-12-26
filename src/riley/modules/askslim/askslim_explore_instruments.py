#!/usr/bin/env python3
"""
askSlim Instrument Explorer
Navigate to Futures Hub and list all available instruments.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

# Configuration
ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
ASKSLIM_HEADLESS = os.getenv("ASKSLIM_HEADLESS", "false").lower() == "true"

# Storage state path
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv(
    "ASKSLIM_STORAGE_STATE_PATH",
    str(DEFAULT_STORAGE_STATE_PATH)
)


def explore_instruments():
    """Explore instruments available in Futures Hub."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        raise FileNotFoundError(
            f"Session state file not found: {storage_state_path}\n"
            "Please run askslim_login.py first."
        )

    print(f"Loading session state from: {storage_state_path}")
    print(f"Navigating to Futures Hub...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=ASKSLIM_HEADLESS)
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()

        try:
            # Navigate to Futures Hub
            page.goto(f"{ASKSLIM_BASE_URL}/futures-hub/", wait_until="networkidle", timeout=30000)

            print(f"\nCurrent URL: {page.url}")
            print("\nSearching for instruments...")

            # Wait a moment for dynamic content
            page.wait_for_timeout(2000)

            # Try to find instrument names/links
            # Common patterns for instrument listings
            selectors_to_try = [
                "h2",  # Instrument names often in h2
                "h3",
                ".instrument",
                ".symbol",
                "[data-symbol]",
                "a[href*='futures']",
            ]

            found_instruments = set()

            for selector in selectors_to_try:
                try:
                    elements = page.query_selector_all(selector)
                    print(f"\nTrying selector: {selector} (found {len(elements)} elements)")

                    for elem in elements:
                        text = elem.inner_text().strip()
                        if text and len(text) < 50:  # Reasonable instrument name length
                            found_instruments.add(text)
                            print(f"  - {text}")
                except Exception as e:
                    pass

            # Print all unique instruments found
            print("\n" + "="*60)
            print("ALL INSTRUMENTS FOUND:")
            print("="*60)
            for inst in sorted(found_instruments):
                print(f"  - {inst}")

            # Take screenshot
            screenshot_path = Path(__file__).parent.parent.parent.parent.parent / "artifacts" / "askslim" / "futures_hub.png"
            page.screenshot(path=str(screenshot_path))
            print(f"\nScreenshot saved: {screenshot_path}")

            # Save HTML
            html_path = Path(__file__).parent.parent.parent.parent.parent / "artifacts" / "askslim" / "futures_hub.html"
            with open(html_path, 'w') as f:
                f.write(page.content())
            print(f"HTML saved: {html_path}")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    try:
        explore_instruments()
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
