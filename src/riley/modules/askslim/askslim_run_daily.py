#!/usr/bin/env python3
"""
askSlim Daily Run
Daily job to scrape askSlim data and update Riley database.
"""

import sys
from pathlib import Path

# Import our modules
from src.riley.modules.askslim.askslim_smoketest import verify_session
from src.riley.modules.askslim.askslim_scraper import run_scraper


def run_daily_scrape():
    """
    Run the daily scraping job.

    1. Verify session is still valid
    2. Run the askSlim scraper to get cycle data
    """
    print("="*60)
    print("askSlim Daily Run - Complete Scrape")
    print("="*60)

    # Verify session is still valid
    print("\n1. Verifying session state...")
    try:
        is_valid = verify_session(headless=True)
        if not is_valid:
            print("✗ Session is invalid - please run askslim_login.py")
            return False
    except FileNotFoundError as e:
        print(f"✗ {e}")
        print("Please run askslim_login.py first to create a session")
        return False
    except Exception as e:
        print(f"✗ Session verification failed: {e}")
        return False

    print("✓ Session is valid")

    # Run the actual scraper
    print("\n2. Running askSlim scraper...")
    print("   This will:")
    print("   - Navigate to Futures Hub and Equities Hub")
    print("   - Extract cycle data for all instruments")
    print("   - Download cycle charts")
    print("   - Update Riley database with cycle specs")
    print("")

    try:
        run_scraper(headless=True)
        print("\n✓ Scraping completed successfully")
    except Exception as e:
        print(f"\n✗ Scraping failed: {e}")
        return False

    print("\n" + "="*60)
    print("Daily run completed successfully")
    print("="*60)

    return True


def main():
    """Main entry point."""
    try:
        success = run_daily_scrape()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
