#!/usr/bin/env python3
"""
Riley Set Cycle - Canonical Cycle Median Setter

THE ONLY WAY Bernard should change cycle inputs.
Every change triggers deterministic rebuild + validation.

Usage:
    python3 scripts/riley_set_cycle.py ES DAILY 2025-12-28
    python3 scripts/riley_set_cycle.py ES WEEKLY 2026-01-04
    python3 scripts/riley_set_cycle.py PL DAILY 2025-12-24 --bump  # Create new version
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.riley.cycle_service import CycleService
from src.riley.cycle_validation import CycleValidationError


def main():
    parser = argparse.ArgumentParser(
        description="Set cycle median (canonical write API)"
    )
    parser.add_argument("symbol", help="Instrument symbol (e.g., ES, PL)")
    parser.add_argument("timeframe", choices=['DAILY', 'WEEKLY'], help="Timeframe")
    parser.add_argument("median", help="Median date (YYYY-MM-DD)")
    parser.add_argument("--bump", action="store_true",
                       help="Bump version (default: replace existing)")
    parser.add_argument("--cycle-length", type=int,
                       help="Cycle length in bars (optional)")
    parser.add_argument("--window-minus", type=int, default=3,
                       help="Bars before median (default: 3)")
    parser.add_argument("--window-plus", type=int, default=3,
                       help="Bars after median (default: 3)")
    parser.add_argument("--prewindow-lead", type=int, default=2,
                       help="Prewindow lead bars (default: 2)")
    parser.add_argument("--source", help="Source of this cycle (optional)")

    args = parser.parse_args()

    print("=" * 60)
    print("RILEY SET CYCLE - CANONICAL WRITE API")
    print("=" * 60)

    # Validate date format
    try:
        datetime.strptime(args.median, '%Y-%m-%d')
    except ValueError:
        print(f"✗ Invalid date format: {args.median}")
        print("  Expected: YYYY-MM-DD (e.g., 2025-12-28)")
        sys.exit(1)

    # Initialize service
    project_root = Path(__file__).parent.parent
    db_path = project_root / "db" / "riley.sqlite"
    service = CycleService(str(db_path))

    # Set cycle median
    print(f"\nSetting cycle for {args.symbol} {args.timeframe}...")
    print(f"  Median: {args.median}")
    print(f"  Window: ±{args.window_minus}/{args.window_plus} bars")
    print(f"  Versioning: {'BUMP' if args.bump else 'REPLACE'}")

    try:
        result = service.set_cycle_median(
            symbol=args.symbol,
            timeframe=args.timeframe,
            median_label=args.median,
            cycle_length_bars=args.cycle_length,
            window_minus_bars=args.window_minus,
            window_plus_bars=args.window_plus,
            prewindow_lead_bars=args.prewindow_lead,
            source=args.source,
            versioning='BUMP' if args.bump else 'REPLACE'
        )

        print("\n✓ SUCCESS")
        print(f"  Version: v{result['version']}")
        print(f"  Median (snapped): {result['median_snapped']}")
        print(f"  Window: {result['window_start']} to {result['window_end']}")

        if args.timeframe == 'DAILY':
            indices = result['indices']['td']
            print(f"  TD indices: {indices['start']} to {indices['end']} (median: {indices['median']})")
        else:
            indices = result['indices']['tw']
            print(f"  TW indices: {indices['start']} to {indices['end']} (median: {indices['median']})")

        print(f"\nCycle updated successfully. Projection rebuilt and validated.")
        sys.exit(0)

    except CycleValidationError as e:
        print(f"\n✗ VALIDATION FAILED")
        print(str(e))
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
