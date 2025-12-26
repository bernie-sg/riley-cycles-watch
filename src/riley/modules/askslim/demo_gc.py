#!/usr/bin/env python3
"""
Demonstration: Scrape GC (Gold) from askSlim
Shows the complete workflow for a single instrument.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from askslim_scraper import run_scraper, ASKSLIM_TO_RILEY, scrape_instrument
from playwright.sync_api import sync_playwright
import os
from dotenv import load_dotenv
import sqlite3

load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "db" / "riley.sqlite"
MEDIA_PATH = PROJECT_ROOT / "media"

def show_gc_database_info():
    """Show what's stored in the database for GC."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("GC (Gold) - DATABASE RECORDS")
    print("="*70)

    # Get instrument info
    cursor.execute("""
        SELECT instrument_id, canonical_symbol, name
        FROM instruments
        WHERE canonical_symbol = 'GC'
    """)

    instrument = cursor.fetchone()
    if not instrument:
        print("❌ GC not found in instruments table")
        conn.close()
        return

    instrument_id, symbol, name = instrument
    print(f"\nInstrument: {name} ({symbol})")
    print(f"ID: {instrument_id}")

    # Get cycle specs
    cursor.execute("""
        SELECT
            cycle_id,
            timeframe,
            anchor_input_date_label,
            cycle_length_bars,
            source,
            version,
            status,
            created_at
        FROM cycle_specs
        WHERE instrument_id = ?
        ORDER BY timeframe, version DESC
    """, (instrument_id,))

    specs = cursor.fetchall()

    if not specs:
        print("\n❌ No cycle specs found")
    else:
        print(f"\n📊 Cycle Specifications: {len(specs)} records")
        print("-" * 70)

        for spec in specs:
            cycle_id, tf, anchor, length, source, version, status, created = spec
            status_icon = "✅" if status == "ACTIVE" else "📦"
            print(f"{status_icon} {tf:7} | Anchor: {anchor} | Length: {length:3} bars | v{version} | {source}")

    conn.close()

def show_gc_charts():
    """Show what charts were downloaded for GC."""
    print("\n" + "="*70)
    print("GC (Gold) - CHART FILES")
    print("="*70)

    gc_media_path = MEDIA_PATH / "GC"

    if not gc_media_path.exists():
        print("\n❌ No media folder found for GC")
        return

    charts = list(gc_media_path.glob("*.png"))

    if not charts:
        print("\n❌ No charts found")
    else:
        print(f"\n📈 Charts: {len(charts)} files")
        print("-" * 70)

        for chart in sorted(charts, key=lambda x: x.stat().st_mtime, reverse=True):
            size_kb = chart.stat().st_size / 1024
            mtime = chart.stat().st_mtime
            from datetime import datetime
            mod_time = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  {chart.name:30} | {size_kb:6.1f} KB | {mod_time}")

def demo_gc_scrape():
    """Demonstrate scraping GC (Gold) only."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("DEMO: Scraping GC (Gold) from askSlim")
    print("="*70)
    print()
    print("This demonstration will:")
    print("  1. Navigate to Futures Hub")
    print("  2. Click on /GC (Gold)")
    print("  3. Extract cycle data:")
    print("     - Weekly cycle low date")
    print("     - Daily cycle low date")
    print("     - Weekly dominant cycle length (bars)")
    print("     - Daily dominant cycle length (bars)")
    print("  4. Download weekly and daily charts")
    print("  5. Update Riley database")
    print()
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,  # Visible browser for demo
            slow_mo=1000     # Slow down to see what's happening
        )
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            # Navigate to Futures Hub
            print("\n📡 Navigating to Futures Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/futures-hub/", wait_until="networkidle")

            # Wait for page to load
            print("⏳ Waiting for page to load...")
            import time
            time.sleep(3)

            # Find the futures hub iframe
            print("🔍 Looking for futures hub iframe...")
            iframe_element = page.wait_for_selector("iframe.fuhub-frame", timeout=15000)
            print("✓ Found iframe")

            # Get the iframe's content frame
            iframe = iframe_element.content_frame()
            print("✓ Got iframe content")

            # Wait for instruments to load inside iframe
            print("⏳ Waiting for instruments to load...")
            time.sleep(5)

            # Wait for instruments to be visible
            iframe.wait_for_selector("text=/GC", timeout=15000)
            print("✓ Instruments loaded")

            # Scrape GC
            print("\n" + "="*70)
            print("Starting GC scrape...")
            print("="*70)

            result = scrape_instrument(page, "/GC", iframe)

            if result:
                print("\n" + "="*70)
                print("✅ DEMO SUCCESSFUL")
                print("="*70)
                print(f"\n📊 Data Extracted:")
                print(f"  Symbol: {result['askslim_symbol']} → {result['riley_symbol']}")
                print(f"  Weekly: {result['weekly_date']} ({result['weekly_length']} bars)")
                print(f"  Daily:  {result['daily_date']} ({result['daily_length']} bars)")

                # Show database info
                show_gc_database_info()

                # Show charts
                show_gc_charts()

                print("\n" + "="*70)
                print("Demo complete! Browser will stay open for 10 seconds...")
                print("="*70)

                time.sleep(10)

                return True
            else:
                print("\n" + "="*70)
                print("❌ DEMO FAILED")
                print("="*70)
                return False

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    # First show current database state
    print("\n🔍 Current Database State:")
    show_gc_database_info()
    show_gc_charts()

    print("\n" + "="*70)
    input("Press Enter to run live scraping demo...")
    print("="*70)

    # Run the demo
    success = demo_gc_scrape()

    sys.exit(0 if success else 1)
