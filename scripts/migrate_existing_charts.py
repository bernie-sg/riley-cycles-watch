#!/usr/bin/env python3
"""
Migrate existing askSlim charts to categorized folder structure
and populate media_files database table.
"""

import sys
from pathlib import Path
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.database import Database

def migrate_charts():
    """Move existing charts to askslim subdirectories and track in DB"""

    media_path = project_root / "media"
    if not media_path.exists():
        print("No media directory found")
        return

    db = Database()
    moved_count = 0
    tracked_count = 0

    # Pattern for askSlim charts
    askslim_pattern = re.compile(r'^(weekly|daily)_\d{8}\.png$')

    for symbol_dir in sorted(media_path.iterdir()):
        if not symbol_dir.is_dir() or symbol_dir.name.startswith('.'):
            continue

        symbol = symbol_dir.name
        askslim_dir = symbol_dir / "askslim"

        # Find askSlim charts in root symbol directory
        for chart_file in symbol_dir.glob("*.png"):
            if askslim_pattern.match(chart_file.name):
                # This is an askSlim chart, move it
                askslim_dir.mkdir(exist_ok=True)
                new_path = askslim_dir / chart_file.name

                # Move file
                chart_file.rename(new_path)
                moved_count += 1
                print(f"  Moved: {symbol}/{chart_file.name} → {symbol}/askslim/{chart_file.name}")

                # Extract timeframe and date
                match = re.match(r'(weekly|daily)_(\d{8})\.png', chart_file.name)
                if match:
                    timeframe = match.group(1).upper()
                    date_str = match.group(2)
                    upload_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

                    # Track in database
                    try:
                        db.insert_media_file(
                            instrument_symbol=symbol,
                            category='askslim',
                            timeframe=timeframe,
                            file_path=str(new_path),
                            file_name=chart_file.name,
                            upload_date=upload_date,
                            source='scraper'
                        )
                        tracked_count += 1
                    except Exception as e:
                        print(f"  ⚠ Failed to track {symbol}/{chart_file.name}: {e}")

    db.close()

    print(f"\n✅ Migration complete:")
    print(f"   Moved: {moved_count} charts")
    print(f"   Tracked: {tracked_count} charts in database")

if __name__ == "__main__":
    migrate_charts()
