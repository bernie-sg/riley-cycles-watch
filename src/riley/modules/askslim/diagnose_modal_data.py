#!/usr/bin/env python3
"""
Diagnostic script to examine the modal HTML structure.
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import time

load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "askslim"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def diagnose_modal():
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            print("1. Navigate to Futures Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/futures-hub/", wait_until="networkidle")
            time.sleep(3)

            print("2. Find iframe...")
            iframe_element = page.wait_for_selector("iframe.fuhub-frame", timeout=15000)
            iframe = iframe_element.content_frame()
            print("✓ Got iframe")

            time.sleep(5)

            print("3. Wait for SPX...")
            iframe.wait_for_selector("text=SPX", timeout=15000)
            print("✓ SPX visible")

            print("4. Click SPX...")
            button = iframe.locator("text=SPX").first
            button.wait_for(state="visible", timeout=5000)
            button.click()
            print("✓ Clicked SPX")

            time.sleep(2)

            # Determine modal context
            modal_context = None
            try:
                page.wait_for_selector("text=Technical Overview", timeout=5000)
                modal_context = page
                print("✓ Modal in main page")
            except:
                iframe.wait_for_selector("text=Technical Overview", timeout=5000)
                modal_context = iframe
                print("✓ Modal in iframe")

            time.sleep(1)

            print("5. Click TECHNICAL DETAILS...")
            tech_tab = modal_context.wait_for_selector("text=TECHNICAL DETAILS", timeout=5000)
            tech_tab.click()
            print("✓ Switched to TECHNICAL DETAILS")

            time.sleep(2)

            print("6. Expand Cycle Low Dates...")
            cycle_dates_section = modal_context.wait_for_selector("text=Cycle Low Dates", timeout=5000)
            cycle_dates_section.click()
            print("✓ Expanded Cycle Low Dates")

            time.sleep(2)

            # Get HTML content of modal
            print("\n7. Extracting Cycle Low Dates HTML...")
            modal_html = modal_context.content()

            # Save full modal HTML
            with open(ARTIFACTS_DIR / "modal_cycle_dates.html", "w") as f:
                f.write(modal_html)
            print(f"✓ Saved full HTML to modal_cycle_dates.html")

            # Extract just the Cycle Low Dates section text
            print("\n8. Searching for date patterns...")
            all_text = modal_context.evaluate("document.body.textContent")

            # Look for patterns like MM/DD/YY
            import re
            dates_found = re.findall(r'\b\d{1,2}/\d{1,2}/\d{2}\b', all_text)
            print(f"Found {len(dates_found)} date patterns:")
            for d in dates_found[:10]:
                print(f"  - {d}")

            # Search for "Weekly" and "Daily" with context
            lines = all_text.split('\n')
            print("\n9. Lines containing 'Weekly':")
            for i, line in enumerate(lines):
                if 'Weekly' in line and ('/' in line or i < len(lines) - 1):
                    print(f"  Line {i}: {line[:100]}")
                    if i < len(lines) - 1:
                        print(f"  Next:    {lines[i+1][:100]}")

            print("\n10. Lines containing 'Daily':")
            for i, line in enumerate(lines):
                if 'Daily' in line and ('/' in line or i < len(lines) - 1):
                    print(f"  Line {i}: {line[:100]}")
                    if i < len(lines) - 1:
                        print(f"  Next:    {lines[i+1][:100]}")

            # Expand Cycle Counts
            print("\n11. Expand Cycle Counts...")
            cycle_dates_section.click()  # Collapse dates first
            time.sleep(1)
            cycle_counts_section = modal_context.wait_for_selector("text=Cycle Counts", timeout=5000)
            cycle_counts_section.click()
            print("✓ Expanded Cycle Counts")

            time.sleep(2)

            # Get updated HTML
            modal_html = modal_context.content()
            with open(ARTIFACTS_DIR / "modal_cycle_counts.html", "w") as f:
                f.write(modal_html)
            print(f"✓ Saved HTML to modal_cycle_counts.html")

            # Search for "bars"
            all_text = modal_context.evaluate("document.body.textContent")
            print("\n12. Lines containing 'bars':")
            lines = all_text.split('\n')
            for i, line in enumerate(lines):
                if 'bars' in line.lower() or 'cycle' in line.lower():
                    print(f"  Line {i}: {line[:150]}")

            # Keep browser open
            print("\n" + "="*70)
            print("Check the browser and HTML files.")
            print("Press Ctrl+C to close...")
            print("="*70)

            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nClosing...")

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    diagnose_modal()
