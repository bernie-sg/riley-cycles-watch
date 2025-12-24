#!/usr/bin/env python3
"""Generate watchlist snapshot for an instrument"""
import sys
import argparse
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.database import Database
from riley.views import generate_watchlist_snapshot


def main():
    parser = argparse.ArgumentParser(description="Generate watchlist snapshot")
    parser.add_argument('--symbol', required=True, help='Instrument symbol')
    parser.add_argument('--asof', required=True, help='As-of trading date (YYYY-MM-DD)')
    parser.add_argument('--notes-limit', type=int, default=3, help='Number of recent notes')
    parser.add_argument('--out-root', default='reports', help='Output root directory')
    args = parser.parse_args()

    db = Database()
    out_root = project_root / args.out_root

    print(f"Generating watchlist snapshot for {args.symbol} as of {args.asof}")

    snapshot = generate_watchlist_snapshot(
        db=db,
        symbol=args.symbol,
        asof_td_label=args.asof,
        notes_limit=args.notes_limit,
        out_root=out_root
    )

    if snapshot.get('status') in ['MISSING_CALENDAR', 'INVALID_ASOF_DATE']:
        print(f"✗ {snapshot['status']}: {snapshot.get('message')}")
        return 1

    out_dir = out_root / "watchlist" / args.symbol / args.asof
    print(f"✓ Snapshot written to {out_dir}")
    print(f"  - snapshot.md")
    print(f"  - snapshot.json")

    db.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
