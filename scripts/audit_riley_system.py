#!/usr/bin/env python3
"""
Riley System Audit - Ground Truth Snapshot

Prints status of all instruments including:
- Daily/weekly medians, windows, status, countdown
- Overlap flags
- Raw cycle data for ES, NQ, PL, BTC
- Notes history
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import CyclesDB
import sqlite3


def main():
    db = CyclesDB()

    # Get latest scan date
    scan_date = db.get_latest_scan_date()

    print("=" * 80)
    print("RILEY SYSTEM AUDIT - GROUND TRUTH")
    print("=" * 80)
    print(f"Scan Date: {scan_date}")
    print(f"Audit Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    # Get all instruments with their status
    df = db.get_today_rows(scan_date)

    print("=" * 80)
    print("ALL INSTRUMENTS STATUS")
    print("=" * 80)
    print()

    for _, row in df.iterrows():
        symbol = row['symbol']
        print(f"Symbol: {symbol}")
        print(f"  Name: {row.get('name', 'N/A')}")
        print(f"  Group: {row.get('group_name', 'N/A')}")
        print(f"  Sector: {row.get('sector', 'N/A')}")
        print()
        print(f"  DAILY:")
        print(f"    Median: {row.get('daily_median', 'N/A')}")
        print(f"    Window: {row.get('daily_start', 'N/A')} → {row.get('daily_end', 'N/A')}")
        print(f"    Status: {row.get('daily_status', 'N/A')}")
        print(f"    Days to core start: {row.get('days_to_daily_core_start', 'N/A')}")
        print()
        print(f"  WEEKLY:")
        print(f"    Median: {row.get('weekly_median', 'N/A')}")
        print(f"    Window: {row.get('weekly_start', 'N/A')} → {row.get('weekly_end', 'N/A')}")
        print(f"    Status: {row.get('weekly_status', 'N/A')}")
        print(f"    Weeks to core start: {row.get('weeks_to_weekly_core_start', 'N/A')}")
        print()
        print(f"  Overlap Flag: {row.get('overlap_flag', 0)}")
        print("-" * 80)
        print()

    # Raw cycle data for specific instruments
    print("=" * 80)
    print("RAW CYCLE DATA (ES, NQ, PL, BTC)")
    print("=" * 80)
    print()

    conn = db._get_connection()
    cursor = conn.cursor()

    for symbol in ['ES', 'NQ', 'PL', 'BTC']:
        print(f"=== {symbol} ===")

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        if not row:
            print(f"  {symbol} not found in database")
            print()
            continue

        instrument_id = row['instrument_id']

        # Get DAILY cycle
        cursor.execute("""
            SELECT
                cs.cycle_id,
                cs.timeframe,
                cs.median_input_date_label,
                cs.cycle_length_bars,
                cs.window_minus_bars,
                cs.window_plus_bars,
                cs.prewindow_lead_bars,
                cs.status,
                cs.version,
                cp.median_label,
                cp.core_start_label,
                cp.core_end_label,
                cp.prewindow_start_label,
                cp.prewindow_end_label
            FROM cycle_specs cs
            LEFT JOIN cycle_projections cp
                ON cp.instrument_id = cs.instrument_id
                AND cp.timeframe = cs.timeframe
                AND cp.version = cs.version
                AND cp.k = 0
                AND cp.active = 1
            WHERE cs.instrument_id = ?
                AND cs.timeframe = 'DAILY'
                AND cs.status = 'ACTIVE'
        """, (instrument_id,))

        daily = cursor.fetchone()
        if daily:
            print(f"  DAILY (cycle_id={daily['cycle_id']}, v{daily['version']}):")
            print(f"    Input median: {daily['median_input_date_label']}")
            print(f"    Snapped median: {daily['median_label']}")
            print(f"    Bars: {daily['cycle_length_bars']}")
            print(f"    Window: ±{daily['window_minus_bars']}/{daily['window_plus_bars']} bars")
            print(f"    Prewindow: {daily['prewindow_lead_bars']} bars before")
            print(f"    Core window: {daily['core_start_label']} → {daily['core_end_label']}")
            print(f"    Prewindow: {daily['prewindow_start_label']} → {daily['prewindow_end_label']}")
        else:
            print(f"  DAILY: No active cycle")

        print()

        # Get WEEKLY cycle
        cursor.execute("""
            SELECT
                cs.cycle_id,
                cs.timeframe,
                cs.median_input_date_label,
                cs.cycle_length_bars,
                cs.window_minus_bars,
                cs.window_plus_bars,
                cs.prewindow_lead_bars,
                cs.status,
                cs.version,
                cp.median_label,
                cp.core_start_label,
                cp.core_end_label,
                cp.prewindow_start_label,
                cp.prewindow_end_label
            FROM cycle_specs cs
            LEFT JOIN cycle_projections cp
                ON cp.instrument_id = cs.instrument_id
                AND cp.timeframe = cs.timeframe
                AND cp.version = cs.version
                AND cp.k = 0
                AND cp.active = 1
            WHERE cs.instrument_id = ?
                AND cs.timeframe = 'WEEKLY'
                AND cs.status = 'ACTIVE'
        """, (instrument_id,))

        weekly = cursor.fetchone()
        if weekly:
            print(f"  WEEKLY (cycle_id={weekly['cycle_id']}, v{weekly['version']}):")
            print(f"    Input median: {weekly['median_input_date_label']}")
            print(f"    Snapped median: {weekly['median_label']}")
            print(f"    Bars: {weekly['cycle_length_bars']}")
            print(f"    Window: ±{weekly['window_minus_bars']}/{weekly['window_plus_bars']} bars")
            print(f"    Prewindow: {weekly['prewindow_lead_bars']} bars before")
            print(f"    Core window: {weekly['core_start_label']} → {weekly['core_end_label']}")
            print(f"    Prewindow: {weekly['prewindow_start_label']} → {weekly['prewindow_end_label']}")
        else:
            print(f"  WEEKLY: No active cycle")

        print()

        # Get notes
        cursor.execute("""
            SELECT
                note_id,
                asof_td_label,
                author,
                source,
                notes,
                created_at,
                updated_at
            FROM desk_notes
            WHERE instrument_id = ?
            ORDER BY asof_td_label DESC
            LIMIT 5
        """, (instrument_id,))

        notes = cursor.fetchall()
        if notes:
            print(f"  NOTES ({len(notes)} most recent):")
            for note in notes:
                print(f"    [{note['asof_td_label']}] by {note['author']} ({note['source']})")
                print(f"      Created: {note['created_at']}")
                print(f"      Updated: {note['updated_at']}")
                note_text = note['notes'] if note['notes'] else ''
                print(f"      Text: {note_text[:100] if note_text else '(empty)'}...")
                print()
        else:
            print(f"  NOTES: None")

        print()

    conn.close()

    # Summary statistics
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()

    total = len(df)
    activated = len(df[(df['daily_status'] == 'ACTIVATED') | (df['weekly_status'] == 'ACTIVATED')])
    prewindow = len(df[(df['daily_status'] == 'PREWINDOW') | (df['weekly_status'] == 'PREWINDOW')])
    overlap = len(df[df['overlap_flag'] == 1])
    both_none = len(df[(df['daily_status'] == 'NONE') & (df['weekly_status'] == 'NONE')])

    print(f"Total instruments: {total}")
    print(f"  At least one ACTIVATED: {activated}")
    print(f"  At least one PREWINDOW: {prewindow}")
    print(f"  Overlap flag = 1: {overlap}")
    print(f"  Both NONE: {both_none}")
    print()

    # Expected priority count
    priority_count = len(df[
        (df['daily_status'].isin(['PREWINDOW', 'ACTIVATED'])) |
        (df['weekly_status'].isin(['PREWINDOW', 'ACTIVATED']))
    ])
    print(f"Expected priority instruments (PREWINDOW or ACTIVATED): {priority_count}")
    print()

    # List priority instruments
    priority_df = df[
        (df['daily_status'].isin(['PREWINDOW', 'ACTIVATED'])) |
        (df['weekly_status'].isin(['PREWINDOW', 'ACTIVATED']))
    ]

    if not priority_df.empty:
        print("Priority instruments:")
        for _, row in priority_df.iterrows():
            print(f"  {row['symbol']:8} D:{row['daily_status']:10} W:{row['weekly_status']:10} Overlap:{row['overlap_flag']}")

    print()
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
