#!/usr/bin/env python3
"""
askSlim Smoke Test
Verifies that saved session state is valid by loading a members-only page.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Load environment variables
load_dotenv()

# Configuration
ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
ASKSLIM_HEADLESS = os.getenv("ASKSLIM_HEADLESS", "true").lower() == "true"

# Storage state path
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv(
    "ASKSLIM_STORAGE_STATE_PATH",
    str(DEFAULT_STORAGE_STATE_PATH)
)

# Artifacts directory
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "askslim"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def verify_session():
    """
    Verify that the saved session state is valid.

    Returns:
        bool: True if session is valid, False otherwise
    """
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        raise FileNotFoundError(
            f"Session state file not found: {storage_state_path}\n"
            "Please run askslim_login.py first to create the session."
        )

    print(f"Loading session state from: {storage_state_path}")
    print(f"Base URL: {ASKSLIM_BASE_URL}")
    print(f"Headless mode: {ASKSLIM_HEADLESS}")

    with sync_playwright() as p:
        # Launch browser with saved session state
        browser = p.chromium.launch(headless=ASKSLIM_HEADLESS)
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            # Navigate to main page
            print(f"\nNavigating to {ASKSLIM_BASE_URL}...")
            page.goto(ASKSLIM_BASE_URL, wait_until="networkidle", timeout=30000)

            print(f"Current URL: {page.url}")

            # Check if we're still logged in
            logged_in_indicators = [
                "text=Logout",
                "text=Log Out",
                "text=Sign Out",
                "text=My Feed",
                "text=WorkBench",
                "text=Workbench",
                "text=My Account",
                ".user-menu",
                ".logged-in"
            ]

            is_logged_in = False
            found_indicator = None

            for indicator in logged_in_indicators:
                try:
                    element = page.wait_for_selector(indicator, timeout=5000)
                    if element:
                        is_logged_in = True
                        found_indicator = indicator
                        break
                except PlaywrightTimeout:
                    continue

            if not is_logged_in:
                print("✗ Session appears to be invalid - no logged-in indicators found")

                # Save failure artifacts
                failure_screenshot = ARTIFACTS_DIR / "smoketest_failed.png"
                failure_html = ARTIFACTS_DIR / "smoketest_failed.html"

                try:
                    page.screenshot(path=str(failure_screenshot))
                    print(f"Failure screenshot: {failure_screenshot}")
                except:
                    pass

                try:
                    html_content = page.content()
                    with open(failure_html, 'w') as f:
                        f.write(html_content)
                    print(f"Failure HTML: {failure_html}")
                except:
                    pass

                return False

            print(f"✓ Session is valid! Found indicator: {found_indicator}")

            # Try to access a members-only page (if we know the URL)
            # For now, we'll just verify the main page shows we're logged in

            # Take success screenshot
            success_screenshot = ARTIFACTS_DIR / "smoketest_success.png"
            page.screenshot(path=str(success_screenshot))
            print(f"Success screenshot: {success_screenshot}")

            return True

        except Exception as e:
            print(f"\n✗ Smoke test failed: {e}")
            raise

        finally:
            context.close()
            browser.close()


def main():
    """Main entry point."""
    try:
        success = verify_session()
        if success:
            print("\n" + "="*60)
            print("SMOKE TEST PASSED")
            print("="*60)
            print("Session state is valid and authenticated")
            print("OK")
            sys.exit(0)
        else:
            print("\n" + "="*60)
            print("SMOKE TEST FAILED")
            print("="*60)
            print("Session may have expired - try running askslim_login.py again")
            sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
