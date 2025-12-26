#!/usr/bin/env python3
"""
Test alternative selector strategies to find SPX button.
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

def test_alternative_selectors():
    """Try different ways to find and click SPX."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("TESTING ALTERNATIVE SELECTOR STRATEGIES")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500
        )
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            print("\n1. Navigate to Futures Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/futures-hub/", wait_until="networkidle")

            print("2. Wait 7 seconds for JS rendering...")
            time.sleep(7)

            print("3. Scroll page...")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(3)

            # Strategy 1: Check for iframes
            print("\n" + "="*70)
            print("STRATEGY 1: Check for iframes")
            print("="*70)
            frames = page.frames
            print(f"Found {len(frames)} frames:")
            for i, frame in enumerate(frames):
                print(f"  Frame {i}: {frame.url}")
                # Try to find SPX in each frame
                try:
                    frame_content = frame.content()
                    if "SPX" in frame_content:
                        print(f"  ✓ Frame {i} contains 'SPX' text!")
                except Exception as e:
                    print(f"  ✗ Could not read frame {i}: {e}")

            # Strategy 2: Get all text content and search
            print("\n" + "="*70)
            print("STRATEGY 2: Search page text content")
            print("="*70)
            page_text = page.evaluate("document.body.textContent")
            if "SPX" in page_text:
                print("✓ 'SPX' found in page text!")
            else:
                print("✗ 'SPX' NOT found in page text")
                print(f"First 500 chars: {page_text[:500]}")

            # Strategy 3: Find all buttons and examine
            print("\n" + "="*70)
            print("STRATEGY 3: Examine all buttons")
            print("="*70)
            buttons = page.query_selector_all("button")
            print(f"Found {len(buttons)} buttons")
            for i, btn in enumerate(buttons[:20]):  # First 20 buttons
                try:
                    btn_text = btn.text_content()
                    if btn_text and "SPX" in btn_text:
                        print(f"  ✓ Button {i} contains 'SPX': {btn_text}")
                        print(f"    Attempting to click...")
                        btn.click()
                        print(f"    ✓ Clicked successfully!")
                        time.sleep(2)
                        return True
                    elif btn_text and btn_text.strip():
                        print(f"  Button {i}: {btn_text[:50]}")
                except Exception as e:
                    pass

            # Strategy 4: Find all clickable elements with SPX
            print("\n" + "="*70)
            print("STRATEGY 4: Find clickable elements containing 'SPX'")
            print("="*70)
            clickables = page.query_selector_all("a, button, div[onclick], div[role='button'], span[onclick]")
            print(f"Found {len(clickables)} potentially clickable elements")
            for i, elem in enumerate(clickables):
                try:
                    elem_text = elem.text_content()
                    if elem_text and "SPX" in elem_text:
                        print(f"  ✓ Element {i} ({elem.evaluate('el => el.tagName')}) contains 'SPX': {elem_text}")
                        print(f"    Attempting to click...")
                        elem.click()
                        print(f"    ✓ Clicked successfully!")
                        time.sleep(2)
                        return True
                except Exception as e:
                    pass

            # Strategy 5: Use JavaScript to find elements
            print("\n" + "="*70)
            print("STRATEGY 5: JavaScript search")
            print("="*70)
            result = page.evaluate("""() => {
                const elements = Array.from(document.querySelectorAll('*'));
                const spxElements = elements.filter(el =>
                    el.textContent && el.textContent.includes('SPX') &&
                    el.textContent.length < 100
                );
                return spxElements.map(el => ({
                    tag: el.tagName,
                    text: el.textContent.trim(),
                    classList: Array.from(el.classList),
                    id: el.id
                }));
            }""")
            print(f"Found {len(result)} elements containing 'SPX':")
            for item in result[:10]:
                print(f"  {item}")

            # Strategy 6: Wait longer and try get_by_text
            print("\n" + "="*70)
            print("STRATEGY 6: Try get_by_text with longer wait")
            print("="*70)
            try:
                spx_elem = page.get_by_text("SPX", exact=True).first
                print("✓ Found SPX element with get_by_text!")
                print("  Waiting for it to be visible...")
                spx_elem.wait_for(state="visible", timeout=5000)
                print("  ✓ Element is visible!")
                print("  Attempting to click...")
                spx_elem.click()
                print("  ✓ Clicked successfully!")
                time.sleep(2)
                return True
            except Exception as e:
                print(f"  ✗ get_by_text failed: {e}")

            # Keep browser open for manual inspection
            print("\n" + "="*70)
            print("All strategies failed. Browser will stay open.")
            print("Press Ctrl+C to close...")
            print("="*70)
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nClosing...")

            return False

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    success = test_alternative_selectors()
    sys.exit(0 if success else 1)
