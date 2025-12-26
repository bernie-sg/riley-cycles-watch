#!/usr/bin/env python3
"""
Manual Navigation Helper
Opens authenticated browser and waits for you to navigate manually.
Use this to discover the correct selectors and navigation path.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import time

load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

def manual_navigation():
    """Open browser and let user navigate manually."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return

    with sync_playwright() as p:
        # Launch visible browser
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100  # Slow down actions for observation
        )

        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )

        page = context.new_page()

        print("="*70)
        print("MANUAL NAVIGATION HELPER")
        print("="*70)
        print()
        print("Browser is now open and authenticated.")
        print()
        print("INSTRUCTIONS:")
        print("1. Navigate to Futures Hub")
        print("2. Click on SPX (or any instrument)")
        print("3. Show me where the 'Technical Details' section is")
        print("4. Show me where the cycle data is")
        print("5. Show me where the Weekly/Daily charts are")
        print()
        print("I will watch your navigation and record the steps.")
        print()
        print("Press Ctrl+C when done to close browser.")
        print("="*70)

        # Start at dashboard
        page.goto(f"{ASKSLIM_BASE_URL}/level3-dashboard/", wait_until="networkidle")

        # Set up console logging
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.text}"))

        # Enable request logging
        page.on("request", lambda req: print(f"[REQUEST] {req.method} {req.url}"))

        try:
            # Keep browser open
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nClosing browser...")
        finally:
            context.close()
            browser.close()
            print("Browser closed.")


if __name__ == "__main__":
    manual_navigation()
