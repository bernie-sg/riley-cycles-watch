#!/usr/bin/env python3
"""
Fix duplicate active cycle projections at k=0.

Problem: Some symbols have multiple active projections at k=0 for the same timeframe,
causing duplicate events in the calendar view.

Solution: For each (symbol, timeframe, k=0) combination with multiple active records,
keep only the most recent projection and deactivate the others.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def fix_duplicate_projections(db_path: str):
    """Fix duplicate active projections in the database."""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔍 Finding duplicate active projections at k=0...\n")

    # Find all duplicate groups
    cursor.execute("""
        SELECT
            i.symbol,
            cp.timeframe,
            i.instrument_id,
            COUNT(*) as count
        FROM cycle_projections cp
        JOIN instruments i ON i.instrument_id = cp.instrument_id
        WHERE cp.k = 0
            AND cp.active = 1
            AND i.active = 1
        GROUP BY i.instrument_id, cp.timeframe
        HAVING COUNT(*) > 1
        ORDER BY i.symbol, cp.timeframe
    """)

    duplicates = cursor.fetchall()

    if not duplicates:
        print("✅ No duplicate projections found. Database is clean.")
        conn.close()
        return

    print(f"❌ Found {len(duplicates)} duplicate groups:\n")
    print("Symbol  | Timeframe | Count")
    print("-" * 35)
    for symbol, timeframe, _, count in duplicates:
        print(f"{symbol:8} | {timeframe:9} | {count}")

    print(f"\n📊 Total duplicate groups: {len(duplicates)}\n")

    # Fix each duplicate group
    fixed_count = 0
    deactivated_count = 0

    for symbol, timeframe, instrument_id, count in duplicates:
        # Get all projections for this group, ordered by projection_id DESC (most recent first)
        cursor.execute("""
            SELECT projection_id, computed_at, median_label
            FROM cycle_projections
            WHERE instrument_id = ?
                AND timeframe = ?
                AND k = 0
                AND active = 1
            ORDER BY projection_id DESC
        """, (instrument_id, timeframe))

        projections = cursor.fetchall()

        if len(projections) <= 1:
            continue  # Shouldn't happen, but safety check

        # Keep the first one (most recent), deactivate the rest
        keep_id = projections[0][0]
        keep_date = projections[0][1]
        keep_median = projections[0][2]

        deactivate_ids = [p[0] for p in projections[1:]]

        print(f"🔧 {symbol} {timeframe}:")
        print(f"   ✅ Keeping projection_id={keep_id} (computed: {keep_date}, median: {keep_median})")

        for proj_id, computed, median in projections[1:]:
            print(f"   ❌ Deactivating projection_id={proj_id} (computed: {computed}, median: {median})")
            cursor.execute("""
                UPDATE cycle_projections
                SET active = 0
                WHERE projection_id = ?
            """, (proj_id,))
            deactivated_count += 1

        print()
        fixed_count += 1

    # Commit changes
    conn.commit()

    print(f"\n✅ Fixed {fixed_count} duplicate groups")
    print(f"✅ Deactivated {deactivated_count} duplicate projections")

    # Verify fix
    print("\n🔍 Verifying fix...\n")
    cursor.execute("""
        SELECT
            i.symbol,
            cp.timeframe,
            COUNT(*) as count
        FROM cycle_projections cp
        JOIN instruments i ON i.instrument_id = cp.instrument_id
        WHERE cp.k = 0
            AND cp.active = 1
            AND i.active = 1
        GROUP BY i.symbol, cp.timeframe
        HAVING COUNT(*) > 1
    """)

    remaining_duplicates = cursor.fetchall()

    if remaining_duplicates:
        print(f"⚠️  WARNING: Still have {len(remaining_duplicates)} duplicate groups!")
        for symbol, timeframe, count in remaining_duplicates:
            print(f"   {symbol} {timeframe}: {count}")
    else:
        print("✅ Verification passed - No more duplicates!")

    conn.close()


if __name__ == "__main__":
    db_path = Path(__file__).parent.parent / "db" / "riley.sqlite"

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        exit(1)

    print(f"📂 Database: {db_path}")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    fix_duplicate_projections(str(db_path))

    print(f"\n🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ Duplicate projections cleanup complete!")
