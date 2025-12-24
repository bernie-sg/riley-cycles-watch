#!/usr/bin/env python3
"""
Smoke Test for DATABASE Page Full Editor

Tests all backend functions:
- get_instrument_full()
- update_cycles()
- update_astro_dates()
- update_desk_note()

Usage:
    python3 scripts/test_database_editor.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import CyclesDB


def test_get_instrument_full():
    """Test getting full instrument data"""
    print("=" * 60)
    print("TEST 1: get_instrument_full()")
    print("=" * 60)

    db = CyclesDB()
    data = db.get_instrument_full('ES')

    print("\n✓ Instrument metadata:")
    print(f"  Symbol: {data['instrument']['symbol']}")
    print(f"  Name: {data['instrument']['name']}")
    print(f"  Sector: {data['instrument']['sector']}")
    print(f"  Active: {data['instrument']['active']}")
    print(f"  Aliases: {data['instrument'].get('aliases')}")

    print("\n✓ DAILY cycle:")
    if data['daily_cycle']:
        print(f"  Median: {data['daily_cycle']['median']}")
        print(f"  Bars: {data['daily_cycle']['bars']}")
        print(f"  Window: {data['daily_cycle']['window_start']} → {data['daily_cycle']['window_end']}")
    else:
        print("  No DAILY cycle configured")

    print("\n✓ WEEKLY cycle:")
    if data['weekly_cycle']:
        print(f"  Median: {data['weekly_cycle']['median']}")
        print(f"  Bars: {data['weekly_cycle']['bars']}")
        print(f"  Window: {data['weekly_cycle']['window_start']} → {data['weekly_cycle']['window_end']}")
    else:
        print("  No WEEKLY cycle configured")

    print("\n✓ Astro dates:")
    print(f"  Primary: {data['astro'].get('primary_date')}")
    print(f"  Backup: {data['astro'].get('backup_date')}")

    print("\n✓ Desk note:")
    print(f"  Text: {data['desk_note']['text'][:100] if data['desk_note']['text'] else 'None'}...")
    print(f"  Updated: {data['desk_note'].get('updated_at')}")

    return data


def test_update_cycles(original_data):
    """Test updating cycles"""
    print("\n" + "=" * 60)
    print("TEST 2: update_cycles()")
    print("=" * 60)

    db = CyclesDB()

    # Calculate new median dates (3 days ahead)
    if original_data['daily_cycle']:
        original_daily = original_data['daily_cycle']['median']
        new_daily = (datetime.strptime(original_daily, '%Y-%m-%d') + timedelta(days=3)).strftime('%Y-%m-%d')
    else:
        new_daily = datetime.now().strftime('%Y-%m-%d')

    if original_data['weekly_cycle']:
        original_weekly = original_data['weekly_cycle']['median']
        new_weekly = (datetime.strptime(original_weekly, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
    else:
        new_weekly = datetime.now().strftime('%Y-%m-%d')

    print(f"\nUpdating cycles:")
    print(f"  DAILY median: {new_daily}")
    print(f"  WEEKLY median: {new_weekly}")

    result = db.update_cycles(
        symbol='ES',
        daily_median=new_daily,
        daily_bars=35,
        weekly_median=new_weekly,
        weekly_bars=36
    )

    if result.get('status') == 'success':
        print("\n✓ Cycles updated successfully!")
        if result.get('daily'):
            print(f"  DAILY window: {result['daily']['window_start']} → {result['daily']['window_end']}")
        if result.get('weekly'):
            print(f"  WEEKLY window: {result['weekly']['window_start']} → {result['weekly']['window_end']}")
    else:
        print(f"\n✗ Failed to update cycles: {result.get('message')}")
        return False

    # Verify changes
    data = db.get_instrument_full('ES')
    print("\n✓ Verification:")
    print(f"  DAILY median in DB: {data['daily_cycle']['median']}")
    print(f"  WEEKLY median in DB: {data['weekly_cycle']['median']}")

    return True


def test_update_astro_dates():
    """Test updating astro dates"""
    print("\n" + "=" * 60)
    print("TEST 3: update_astro_dates()")
    print("=" * 60)

    db = CyclesDB()

    # Set dates 30 and 45 days in the future
    primary = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    backup = (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')

    print(f"\nUpdating astro dates:")
    print(f"  Primary: {primary}")
    print(f"  Backup: {backup}")

    success = db.update_astro_dates(
        symbol='ES',
        primary_date=primary,
        backup_date=backup
    )

    if success:
        print("\n✓ Astro dates updated successfully!")

        # Verify
        data = db.get_instrument_full('ES')
        print("\n✓ Verification:")
        print(f"  Primary in DB: {data['astro'].get('primary_date')}")
        print(f"  Backup in DB: {data['astro'].get('backup_date')}")
    else:
        print("\n✗ Failed to update astro dates")
        return False

    return True


def test_update_desk_note():
    """Test updating desk note"""
    print("\n" + "=" * 60)
    print("TEST 4: update_desk_note()")
    print("=" * 60)

    db = CyclesDB()

    note_text = f"""Test note created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- This is a test bullet point
- Another bullet point
- Testing desk notes editor"""

    print(f"\nUpdating desk note:")
    print(f"  Text: {note_text[:50]}...")

    success = db.update_desk_note(
        symbol='ES',
        note_text=note_text
    )

    if success:
        print("\n✓ Desk note updated successfully!")

        # Verify
        data = db.get_instrument_full('ES')
        print("\n✓ Verification:")
        print(f"  Note text: {data['desk_note']['text'][:100]}...")
        print(f"  Updated at: {data['desk_note'].get('updated_at')}")
    else:
        print("\n✗ Failed to update desk note")
        return False

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("DATABASE EDITOR SMOKE TEST")
    print("=" * 60)

    try:
        # Test 1: Get full data
        original_data = test_get_instrument_full()

        # Test 2: Update cycles
        if not test_update_cycles(original_data):
            print("\n✗ Cycles update test failed")
            sys.exit(1)

        # Test 3: Update astro dates
        if not test_update_astro_dates():
            print("\n✗ Astro dates update test failed")
            sys.exit(1)

        # Test 4: Update desk note
        if not test_update_desk_note():
            print("\n✗ Desk note update test failed")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe DATABASE page full editor is working correctly.")
        print("You can now:")
        print("1. Navigate to DATABASE page in Streamlit")
        print("2. Select ES (or search for SPY alias)")
        print("3. Edit cycles, astro dates, and notes")
        print("4. Verify changes propagate to TODAY and CALENDAR views")

        sys.exit(0)

    except Exception as e:
        print(f"\n✗ TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
