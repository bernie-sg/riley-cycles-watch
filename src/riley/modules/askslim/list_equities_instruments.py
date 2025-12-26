#!/usr/bin/env python3
"""
List all instruments in Equities/ETFs Hub.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import time
import re

load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

def list_instruments():
    """List all available instruments."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("LISTING: All Equities/ETFs Hub Instruments")
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

            # Find iframe
            iframe_element = page.wait_for_selector("iframe.eehub-frame", timeout=15000)
            iframe = iframe_element.content_frame()
            print("✓ Got iframe")
            time.sleep(5)

            # Get all text content
            all_text = iframe.evaluate("document.body.innerText")

            # Parse out instrument sections
            print("\n" + "="*70)
            print("RAW CONTENT:")
            print("="*70)
            print(all_text)

            # Try to find a pattern
            # Look for sections like "Stock Chart Grid #1", etc.
            sections = re.split(r'(Indexes & VIX|Stock Chart Grid #\d+)', all_text)

            instruments = []

            print("\n" + "="*70)
            print("PARSED INSTRUMENTS:")
            print("="*70)

            for i in range(len(sections)):
                section_header = sections[i].strip()
                if section_header in ['Indexes & VIX'] or section_header.startswith('Stock Chart Grid'):
                    if i + 1 < len(sections):
                        section_content = sections[i + 1]
                        print(f"\n{section_header}:")

                        # Parse instrument pairs (symbol + name)
                        # Pattern: SYMBOL followed by Company Name
                        lines = section_content.strip().split('\n')
                        for j in range(0, len(lines), 2):
                            if j + 1 < len(lines):
                                symbol = lines[j].strip()
                                name = lines[j + 1].strip()

                                # Basic validation: symbol should be uppercase, short
                                if symbol.isupper() and len(symbol) <= 6 and len(name) > 0:
                                    instruments.append((symbol, name))
                                    print(f"  {symbol:6} - {name}")

            print("\n" + "="*70)
            print(f"TOTAL INSTRUMENTS FOUND: {len(instruments)}")
            print("="*70)

            # Exclude VIX as requested
            instruments_no_vix = [(s, n) for s, n in instruments if s != 'VIX']
            print(f"\nInstruments to scrape (excluding VIX): {len(instruments_no_vix)}")

            # Generate mapping dict
            print("\n" + "="*70)
            print("PYTHON MAPPING:")
            print("="*70)
            print("ASKSLIM_EQUITIES_TO_RILEY = {")
            for symbol, name in instruments_no_vix:
                # Use symbol as Riley symbol (can be customized later)
                print(f'    "{symbol}": "{symbol}",  # {name}')
            print("}")

            print("\n" + "="*70)
            print("Keeping browser open for 10 seconds...")
            print("="*70)
            time.sleep(10)

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    list_instruments()
