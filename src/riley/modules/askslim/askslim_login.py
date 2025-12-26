#!/usr/bin/env python3
"""
askSlim Login Module
Performs browser automation to log into askslim.com and save authenticated session state.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Load environment variables
load_dotenv()

# Configuration from environment
ASKSLIM_USERNAME = os.getenv("ASKSLIM_USERNAME")
ASKSLIM_PASSWORD = os.getenv("ASKSLIM_PASSWORD")
ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
ASKSLIM_HEADLESS = os.getenv("ASKSLIM_HEADLESS", "false").lower() == "true"

# Default storage state path
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv(
    "ASKSLIM_STORAGE_STATE_PATH",
    str(DEFAULT_STORAGE_STATE_PATH)
)

# Artifacts directory for failure debugging
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "askslim"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def validate_credentials():
    """Validate that required credentials are set."""
    if not ASKSLIM_USERNAME:
        raise ValueError("ASKSLIM_USERNAME environment variable is required")
    if not ASKSLIM_PASSWORD:
        raise ValueError("ASKSLIM_PASSWORD environment variable is required")


def perform_login():
    """
    Perform login to askSlim and save authenticated session state.

    Returns:
        bool: True if login successful, False otherwise
    """
    validate_credentials()

    print(f"Starting askSlim login...")
    print(f"Base URL: {ASKSLIM_BASE_URL}")
    print(f"Username: {ASKSLIM_USERNAME}")
    print(f"Headless mode: {ASKSLIM_HEADLESS}")
    print(f"Storage state path: {ASKSLIM_STORAGE_STATE_PATH}")

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=ASKSLIM_HEADLESS)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()

        try:
            # Navigate directly to WordPress login page
            login_url = f"{ASKSLIM_BASE_URL}/wp-login.php"
            print(f"\nNavigating to {login_url}...")
            page.goto(login_url, wait_until="networkidle", timeout=30000)

            print(f"Current URL: {page.url}")

            # Fill in login form
            print("Filling login credentials...")

            # WordPress login form selectors
            username_selectors = [
                "input[name='log']",  # WordPress default
                "input[name='username']",
                "input[name='email']",
                "input[type='email']",
                "#user_login",  # WordPress default ID
                "#username",
                "#email"
            ]

            password_selectors = [
                "input[name='pwd']",  # WordPress default
                "input[name='password']",
                "input[type='password']",
                "#user_pass",  # WordPress default ID
                "#password"
            ]

            # Find and fill username field
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = page.wait_for_selector(selector, timeout=3000)
                    if username_field:
                        print(f"Found username field: {selector}")
                        username_field.fill(ASKSLIM_USERNAME)
                        break
                except PlaywrightTimeout:
                    continue

            if not username_field:
                raise Exception("Could not find username/email input field")

            # Find and fill password field
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = page.wait_for_selector(selector, timeout=3000)
                    if password_field:
                        print(f"Found password field: {selector}")
                        password_field.fill(ASKSLIM_PASSWORD)
                        break
                except PlaywrightTimeout:
                    continue

            if not password_field:
                raise Exception("Could not find password input field")

            # Submit the form
            print("Submitting login form...")

            submit_selectors = [
                "#wp-submit",  # WordPress default
                "input[name='wp-submit']",  # WordPress default
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Login')",
                "button:has-text('Log In')",
                "button:has-text('Sign In')",
                "button:has-text('Submit')"
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = page.wait_for_selector(selector, timeout=3000)
                    if submit_button:
                        print(f"Found submit button: {selector}")
                        break
                except PlaywrightTimeout:
                    continue

            if submit_button:
                submit_button.click()
            else:
                # Try pressing Enter on password field
                print("No submit button found, pressing Enter...")
                password_field.press("Enter")

            # Wait for navigation after login
            print("Waiting for login to complete...")
            page.wait_for_load_state("networkidle", timeout=15000)

            print(f"Current URL after login attempt: {page.url}")

            # Check if we're logged in
            # Check URL first - WordPress often redirects to wp-admin or member areas
            is_logged_in = False

            if "/wp-admin" in page.url or "/futures-hub" in page.url:
                print(f"✓ Login successful! Redirected to: {page.url}")
                is_logged_in = True
            elif "wp-login.php" in page.url:
                # Still on login page - check for error messages
                print("⚠ Still on login page - checking for errors...")
                is_logged_in = False
            else:
                # Look for common logged-in indicators on the page
                logged_in_indicators = [
                    "text=Logout",
                    "text=Log Out",
                    "text=Sign Out",
                    "text=My Feed",
                    "text=WorkBench",
                    "text=Workbench",
                    "text=My Account",
                    "a[href*='wp-admin']",
                    ".user-menu",
                    ".logged-in",
                    "#wpadminbar"  # WordPress admin bar
                ]

                for indicator in logged_in_indicators:
                    try:
                        element = page.wait_for_selector(indicator, timeout=5000)
                        if element:
                            print(f"✓ Login successful! Found indicator: {indicator}")
                            is_logged_in = True
                            break
                    except PlaywrightTimeout:
                        continue

            if not is_logged_in:
                raise Exception("Login appears to have failed - no logged-in indicators found")

            # Save the authenticated session state
            print(f"\nSaving session state to: {ASKSLIM_STORAGE_STATE_PATH}")
            context.storage_state(path=ASKSLIM_STORAGE_STATE_PATH)

            print("✓ Session state saved successfully!")

            # Take a success screenshot
            success_screenshot = ARTIFACTS_DIR / "login_success.png"
            page.screenshot(path=str(success_screenshot))
            print(f"Success screenshot: {success_screenshot}")

            return True

        except Exception as e:
            print(f"\n✗ Login failed: {e}")

            # Save failure artifacts
            failure_screenshot = ARTIFACTS_DIR / "login_failed.png"
            failure_html = ARTIFACTS_DIR / "login_failed.html"

            try:
                page.screenshot(path=str(failure_screenshot))
                print(f"Failure screenshot saved: {failure_screenshot}")
            except:
                pass

            try:
                html_content = page.content()
                with open(failure_html, 'w') as f:
                    f.write(html_content)
                print(f"Failure HTML saved: {failure_html}")
            except:
                pass

            raise

        finally:
            context.close()
            browser.close()


def main():
    """Main entry point."""
    try:
        success = perform_login()
        if success:
            print("\n" + "="*60)
            print("LOGIN COMPLETE")
            print("="*60)
            print(f"Session state: {ASKSLIM_STORAGE_STATE_PATH}")
            print("You can now run askslim_smoketest.py to verify the session")
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
