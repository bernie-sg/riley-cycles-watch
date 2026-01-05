#!/usr/bin/env python3
"""
askSlim Daily Run
Daily job to scrape askSlim data and update Riley database.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import our modules
from src.riley.modules.askslim.askslim_smoketest import verify_session
from src.riley.modules.askslim.askslim_scraper import run_scraper
from src.riley.modules.askslim.askslim_equities_scraper import run_equities_scraper
from src.riley.cycles_rebuild import CyclesRebuilder


def run_daily_scrape():
    """
    Run the daily scraping job.

    1. Verify session is still valid
    2. Run the askSlim scraper to get cycle data
    3. Rebuild cycle projections for updated specs
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

    # Run the actual scrapers
    print("\n2. Running askSlim scrapers...")
    print("   This will:")
    print("   - Navigate to Futures Hub and Equities Hub")
    print("   - Extract cycle data for all instruments")
    print("   - Download cycle charts")
    print("   - Update Riley database with cycle specs")
    print("")

    try:
        print("\n2a. Running Futures Hub scraper...")
        run_scraper(headless=True)
        print("\n✓ Futures Hub scraping completed")
    except Exception as e:
        print(f"\n✗ Futures Hub scraping failed: {e}")
        return False

    try:
        print("\n2b. Running Equities Hub scraper...")
        run_equities_scraper()
        print("\n✓ Equities Hub scraping completed")
    except Exception as e:
        print(f"\n✗ Equities Hub scraping failed: {e}")
        return False

    # Rebuild cycle projections
    print("\n3. Rebuilding cycle projections...")
    print("   This will deactivate old projections and create new ones")
    print("   based on the updated cycle specs from askSlim")
    print("")

    try:
        rebuilder = CyclesRebuilder()
        results = rebuilder.rebuild_all()

        print(f"\n   Rebuilt: {results['rebuilt']}")
        print(f"   Skipped: {results['skipped']}")
        print(f"   Errors: {results['errors']}")

        if results['errors'] > 0:
            print("\n⚠️  Some projections failed to rebuild (see details above)")
        else:
            print("\n✓ All projections rebuilt successfully")

    except Exception as e:
        print(f"\n✗ Projection rebuild failed: {e}")
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
