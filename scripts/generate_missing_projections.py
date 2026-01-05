#!/usr/bin/env python3
"""Generate missing cycle projections for cycles that have specs but no projections"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.database import Database
from riley.utils.projection_generator import generate_projections_for_cycle

def main():
    db = Database()

    # Find all ACTIVE cycle specs that have no projections
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT
            i.symbol,
            cs.cycle_id,
            cs.timeframe,
            cs.cycle_length_bars
        FROM cycle_specs cs
        JOIN instruments i ON i.instrument_id = cs.instrument_id
        LEFT JOIN cycle_projections cp ON cp.cycle_id = cs.cycle_id
        WHERE cs.status = 'ACTIVE'
        GROUP BY cs.cycle_id
        HAVING COUNT(cp.k) = 0
        ORDER BY i.symbol, cs.timeframe
    """)

    missing = cursor.fetchall()

    if not missing:
        print("✅ All active cycles have projections")
        return

    print(f"Found {len(missing)} cycles missing projections:\n")
    for row in missing:
        symbol, cycle_id, timeframe, length = row
        print(f"  {symbol} {timeframe} (cycle_id={cycle_id}, length={length})")

    print("\nGenerating projections...")

    generated = 0
    for row in missing:
        symbol, cycle_id, timeframe, length = row
        try:
            # Generate projections for k=-2 to +8 (DAILY) or k=-2 to +6 (WEEKLY)
            max_k = 8 if timeframe == 'DAILY' else 6

            # Get cycle spec details
            cursor.execute("""
                SELECT
                    cs.*,
                    i.instrument_id
                FROM cycle_specs cs
                JOIN instruments i ON i.instrument_id = cs.instrument_id
                WHERE cs.cycle_id = ?
            """, (cycle_id,))

            spec = dict(cursor.fetchone())
            instrument_id = spec['instrument_id']

            # Generate projections using the projection generator
            # This will create projections for k=-2..+max_k
            result = generate_projections_for_cycle(
                db=db,
                cycle_id=cycle_id,
                instrument_id=instrument_id,
                timeframe=timeframe,
                anchor_date=spec['anchor_input_date_label'],
                cycle_length=length,
                k_range=range(-2, max_k + 1)
            )

            if result:
                print(f"  ✓ {symbol} {timeframe}: Generated {len(result)} projections")
                generated += 1
            else:
                print(f"  ✗ {symbol} {timeframe}: Failed to generate projections")

        except Exception as e:
            print(f"  ✗ {symbol} {timeframe}: Error - {e}")

    db.conn.commit()
    db.close()

    print(f"\n✅ Generated projections for {generated}/{len(missing)} cycles")

if __name__ == "__main__":
    main()
