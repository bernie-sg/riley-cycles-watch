#!/usr/bin/env python3
"""Add canonical instrument with optional aliases to Cycles Watch"""
import sys
import argparse
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.database import Database


def main():
    parser = argparse.ArgumentParser(description="Add canonical instrument with aliases")
    parser.add_argument('--canonical', required=True, help='Canonical symbol')
    parser.add_argument('--alias', action='append', default=[], help='Alias symbol(s) - can specify multiple times')
    parser.add_argument('--name', help='Instrument name')
    args = parser.parse_args()

    db = Database()
    db.run_migrations()

    # Add canonical
    print(f"Adding canonical instrument: {args.canonical}")
    db.upsert_instrument(
        symbol=args.canonical,
        role='CANONICAL',
        canonical_symbol=args.canonical,
        name=args.name
    )
    print(f"✓ {args.canonical} added as CANONICAL")

    # Add aliases
    for alias_symbol in args.alias:
        print(f"Adding alias: {alias_symbol} -> {args.canonical}")
        db.upsert_instrument(
            symbol=alias_symbol,
            role='ALIAS',
            canonical_symbol=args.canonical,
            alias_of_symbol=args.canonical
        )
        print(f"✓ {alias_symbol} added as ALIAS of {args.canonical}")

    db.close()
    print(f"\n✓ Instrument setup complete")


if __name__ == '__main__':
    sys.exit(main() or 0)
