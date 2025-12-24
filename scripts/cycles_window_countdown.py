#!/usr/bin/env python3
"""Generate window countdown view"""
import sys
import argparse
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.database import Database
from riley.views import generate_window_countdown


def main():
    parser = argparse.ArgumentParser(description="Generate window countdown view")
    parser.add_argument('--asof', required=True, help='As-of trading date (YYYY-MM-DD)')
    parser.add_argument('--horizon-td', type=int, default=15, help='Daily horizon (trading days)')
    parser.add_argument('--horizon-tw', type=int, default=6, help='Weekly horizon (trading weeks)')
    parser.add_argument('--out-root', default='reports', help='Output root directory')
    args = parser.parse_args()

    db = Database()
    out_root = project_root / args.out_root

    print(f"Generating window countdown as of {args.asof}")
    print(f"Horizons: {args.horizon_td} TD, {args.horizon_tw} TW")

    countdown = generate_window_countdown(
        db=db,
        asof_td_label=args.asof,
        horizon_td=args.horizon_td,
        horizon_tw=args.horizon_tw,
        out_root=out_root
    )

    out_dir = out_root / "countdown" / args.asof
    print(f"\n✓ Countdown written to {out_dir}")
    print(f"  - countdown.md")
    print(f"  - countdown.json")
    print(f"\n{len(countdown['rows'])} instruments ranked")

    db.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
