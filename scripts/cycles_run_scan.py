#!/usr/bin/env python3
"""Run daily scan and optionally generate views"""
import sys
import argparse
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.database import Database
from riley.views import generate_watchlist_snapshot, generate_window_countdown


def main():
    parser = argparse.ArgumentParser(description="Run daily scan")
    parser.add_argument('--asof', required=True, help='As-of trading date (YYYY-MM-DD)')
    parser.add_argument('--emit-watchlist', action='store_true', default=True, help='Generate watchlist snapshots')
    parser.add_argument('--emit-countdown', action='store_true', default=True, help='Generate countdown view')
    parser.add_argument('--top', type=int, default=30, help='Top N instruments for watchlist')
    parser.add_argument('--horizon-td', type=int, default=15, help='Daily horizon (trading days)')
    parser.add_argument('--horizon-tw', type=int, default=6, help='Weekly horizon (trading weeks)')
    parser.add_argument('--notes-limit', type=int, default=3, help='Notes per watchlist')
    parser.add_argument('--out-root', default='reports', help='Output root directory')
    args = parser.parse_args()

    db = Database()
    out_root = project_root / args.out_root

    print(f"Running scan for {args.asof}")

    # Get all canonical instruments
    instruments = db.list_canonical_instruments()
    print(f"Found {len(instruments)} canonical instruments")

    # Create scan run
    scan_id = db.create_scan_run(args.asof)
    print(f"Scan ID: {scan_id}")

    # For each instrument, compute status
    scan_rows = []

    for inst in instruments:
        symbol = inst['symbol']

        # Get calendars
        daily_cal = db.get_daily_calendar(symbol)
        if not daily_cal:
            continue

        # Find asof index
        import pandas as pd
        df_daily = pd.DataFrame(daily_cal)
        asof_row = df_daily[df_daily['trading_date_label'] == args.asof]
        if asof_row.empty:
            continue

        asof_td_index = int(asof_row.iloc[0]['td_index'])

        # Get best projection for daily
        daily_proj = db.get_best_projection_for_asof(symbol, 'DAILY', asof_td_index)
        daily_status = 'NONE'
        days_to_daily_core = None

        if daily_proj:
            daily_status, days_to_daily_core = _compute_status(asof_td_index, daily_proj)

        # Get best projection for weekly
        weekly_cal = db.get_weekly_calendar(symbol)
        weekly_status = 'NONE'
        weeks_to_weekly_core = None

        if weekly_cal:
            df_weekly = pd.DataFrame(weekly_cal)
            week_row = df_weekly[df_weekly['week_end_label'] >= args.asof]
            if not week_row.empty:
                asof_tw_index = int(week_row.iloc[0]['tw_index'])
                weekly_proj = db.get_best_projection_for_asof(symbol, 'WEEKLY', asof_tw_index)

                if weekly_proj:
                    weekly_status, weeks_to_weekly_core = _compute_status(asof_tw_index, weekly_proj)

        # Compute priority score
        priority_score = 0
        if daily_status == 'IN_WINDOW' and weekly_status == 'IN_WINDOW':
            priority_score += 100
        elif (daily_status == 'IN_WINDOW' and weekly_status == 'PREWINDOW') or \
             (daily_status == 'PREWINDOW' and weekly_status == 'IN_WINDOW'):
            priority_score += 60
        elif daily_status == 'IN_WINDOW' or weekly_status == 'IN_WINDOW':
            priority_score += 30
        elif daily_status == 'PREWINDOW' or weekly_status == 'PREWINDOW':
            priority_score += 10

        # Overlap flag (simplified - just check if both in window)
        overlap_flag = 1 if (daily_status == 'IN_WINDOW' and weekly_status == 'IN_WINDOW') else 0
        if overlap_flag:
            priority_score += 20

        scan_rows.append({
            'instrument_id': inst['instrument_id'],
            'daily_status': daily_status,
            'weekly_status': weekly_status,
            'days_to_daily_core_start': days_to_daily_core,
            'weeks_to_weekly_core_start': weeks_to_weekly_core,
            'overlap_flag': overlap_flag,
            'priority_score': priority_score,
            'notes': f"{symbol}: D={daily_status}, W={weekly_status}"
        })

    # Write scan rows
    db.create_scan_rows(scan_id, scan_rows)
    print(f"✓ Scan completed: {len(scan_rows)} instruments processed")

    # Sort by priority for display
    scan_rows.sort(key=lambda r: -r['priority_score'])

    # Display top results
    print(f"\nTop {min(10, len(scan_rows))} by priority:")
    for i, row in enumerate(scan_rows[:10], 1):
        inst = next(i for i in instruments if i['instrument_id'] == row['instrument_id'])
        print(f"{i}. {inst['symbol']}: Priority={row['priority_score']}, D={row['daily_status']}, W={row['weekly_status']}")

    # Generate countdown view
    if args.emit_countdown:
        print(f"\nGenerating countdown view...")
        countdown = generate_window_countdown(
            db=db,
            asof_td_label=args.asof,
            horizon_td=args.horizon_td,
            horizon_tw=args.horizon_tw,
            out_root=out_root
        )
        out_dir = out_root / "countdown" / args.asof
        print(f"✓ Countdown: {out_dir}")

    # Generate watchlist snapshots for top N
    if args.emit_watchlist:
        print(f"\nGenerating watchlist snapshots for top {args.top}...")
        top_instruments = scan_rows[:args.top]
        for row in top_instruments:
            inst = next(i for i in instruments if i['instrument_id'] == row['instrument_id'])
            symbol = inst['symbol']

            snapshot = generate_watchlist_snapshot(
                db=db,
                symbol=symbol,
                asof_td_label=args.asof,
                notes_limit=args.notes_limit,
                out_root=out_root
            )

            if snapshot.get('status') not in ['MISSING_CALENDAR', 'INVALID_ASOF_DATE']:
                out_dir = out_root / "watchlist" / symbol / args.asof
                print(f"  ✓ {symbol}: {out_dir}")

    db.close()
    return 0


def _compute_status(asof_index: int, projection: dict) -> tuple:
    """Compute status and distance to core start"""
    pre_start = projection['prewindow_start_index']
    pre_end = projection['prewindow_end_index']
    core_start = projection['core_start_index']
    core_end = projection['core_end_index']

    if pre_start <= asof_index <= pre_end:
        return 'PREWINDOW', core_start - asof_index
    elif core_start <= asof_index <= core_end:
        return 'IN_WINDOW', 0
    elif asof_index > core_end:
        return 'POST', None
    else:
        return 'NONE', core_start - asof_index if asof_index < core_start else None


if __name__ == '__main__':
    sys.exit(main())
