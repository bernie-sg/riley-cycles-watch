#!/usr/bin/env python3
"""
Riley Cycles Repair Script

Rebuild all cycle projections with proper DAILY/WEEKLY calendar separation.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.riley.cycles_rebuild import CyclesRebuilder


def backup_database(db_path: Path):
    """Create timestamped backup"""
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"riley_repair_{timestamp}.sqlite"

    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path


def run_invariant_checks(db_path: Path):
    """Run invariant checks to verify data integrity"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("INVARIANT CHECKS")
    print("=" * 60)

    # Check 1: No duplicate projections
    print("\n1. Checking for duplicate projections...")
    cursor.execute("""
        SELECT instrument_id, timeframe, version, k, COUNT(*) as c
        FROM cycle_projections
        GROUP BY instrument_id, timeframe, version, k
        HAVING c > 1
    """)
    duplicates = cursor.fetchall()
    if duplicates:
        print(f"✗ FAILED: Found {len(duplicates)} duplicate projection groups")
        for dup in duplicates:
            print(f"   - instrument_id={dup['instrument_id']}, "
                  f"timeframe={dup['timeframe']}, version={dup['version']}, "
                  f"k={dup['k']}, count={dup['c']}")
        return False
    else:
        print("✓ PASSED: No duplicate projections")

    # Check 2: Exactly one k=0 per active spec
    print("\n2. Checking for exactly one k=0 per active spec...")
    cursor.execute("""
        SELECT i.symbol, cs.timeframe, cs.version, COUNT(cp.projection_id) as c
        FROM cycle_specs cs
        JOIN instruments i ON i.instrument_id = cs.instrument_id
        LEFT JOIN cycle_projections cp
          ON cp.instrument_id = cs.instrument_id
          AND cp.timeframe = cs.timeframe
          AND cp.version = cs.version
          AND cp.k = 0
          AND cp.active = 1
        WHERE cs.status = 'ACTIVE'
        GROUP BY i.symbol, cs.timeframe, cs.version
        HAVING c <> 1
    """)
    missing_or_extra = cursor.fetchall()
    if missing_or_extra:
        print(f"✗ FAILED: Found {len(missing_or_extra)} specs without exactly one k=0 projection")
        for row in missing_or_extra:
            print(f"   - {row['symbol']} {row['timeframe']} v{row['version']}: count={row['c']}")
        return False
    else:
        print("✓ PASSED: All active specs have exactly one k=0 projection")

    # Check 3: Spot-check PL DAILY
    print("\n3. Spot-checking PL DAILY labels...")
    cursor.execute("""
        WITH pl AS (SELECT instrument_id FROM instruments WHERE symbol='PL')
        SELECT timeframe, version,
               median_label,
               core_start_label, core_end_label,
               median_td_index,
               core_start_td_index, core_end_td_index
        FROM cycle_projections
        JOIN pl ON pl.instrument_id = cycle_projections.instrument_id
        WHERE timeframe='DAILY' AND k=0
    """)
    daily = cursor.fetchone()
    if daily:
        print(f"   Median: {daily['median_label']} (td_index={daily['median_td_index']})")
        print(f"   Window: {daily['core_start_label']} to {daily['core_end_label']}")
        print(f"           (td_index {daily['core_start_td_index']} to {daily['core_end_td_index']})")

        # Verify window is ±3 from median
        expected_start = daily['median_td_index'] - 3
        expected_end = daily['median_td_index'] + 3
        if daily['core_start_td_index'] == expected_start and daily['core_end_td_index'] == expected_end:
            print("   ✓ Window is median ±3 TD bars")
        else:
            print(f"   ✗ Window mismatch: expected {expected_start} to {expected_end}")
            return False
    else:
        print("   - No PL DAILY projection found")

    # Check 4: Spot-check PL WEEKLY
    print("\n4. Spot-checking PL WEEKLY labels...")
    cursor.execute("""
        WITH pl AS (SELECT instrument_id FROM instruments WHERE symbol='PL')
        SELECT timeframe, version,
               median_label,
               core_start_label, core_end_label,
               median_tw_index,
               core_start_tw_index, core_end_tw_index
        FROM cycle_projections
        JOIN pl ON pl.instrument_id = cycle_projections.instrument_id
        WHERE timeframe='WEEKLY' AND k=0
    """)
    weekly = cursor.fetchone()
    if weekly:
        print(f"   Median: {weekly['median_label']} (tw_index={weekly['median_tw_index']})")
        print(f"   Window: {weekly['core_start_label']} to {weekly['core_end_label']}")
        print(f"           (tw_index {weekly['core_start_tw_index']} to {weekly['core_end_tw_index']})")

        # Verify window is ±3 from median
        expected_start = weekly['median_tw_index'] - 3
        expected_end = weekly['median_tw_index'] + 3
        if weekly['core_start_tw_index'] == expected_start and weekly['core_end_tw_index'] == expected_end:
            print("   ✓ Window is median ±3 TW bars")
        else:
            print(f"   ✗ Window mismatch: expected {expected_start} to {expected_end}")
            return False
    else:
        print("   - No PL WEEKLY projection found")

    conn.close()

    print("\n" + "=" * 60)
    print("✓ ALL INVARIANT CHECKS PASSED")
    print("=" * 60)

    return True


def main():
    parser = argparse.ArgumentParser(description="Rebuild cycle projections")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbol", help="Rebuild for specific symbol (e.g., PL, ES)")
    group.add_argument("--all", action="store_true", help="Rebuild all instruments")
    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "db" / "riley.sqlite"

    print("=" * 60)
    print("RILEY CYCLES REPAIR")
    print("=" * 60)

    # Step 1: Backup
    print("\nStep 1: Creating backup...")
    backup_path = backup_database(db_path)

    # Step 2: Rebuild
    print("\nStep 2: Rebuilding projections...")
    print("-" * 60)

    rebuilder = CyclesRebuilder(str(db_path))

    if args.all:
        results = rebuilder.rebuild_all()
    else:
        results = rebuilder.rebuild_all(symbol=args.symbol)

    print("-" * 60)
    print(f"\nResults:")
    print(f"  Rebuilt: {results['rebuilt']}")
    print(f"  Skipped: {results['skipped']}")
    print(f"  Errors:  {results['errors']}")

    if results['errors'] > 0:
        print("\n✗ Rebuild completed with errors")
        sys.exit(1)

    # Step 3: Invariant checks
    print("\nStep 3: Running invariant checks...")
    if not run_invariant_checks(db_path):
        print("\n✗ Invariant checks failed")
        sys.exit(1)

    print("\n✓ Cycles repair completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
