#!/usr/bin/env python3
"""
Riley Project - Single Instrument Pipeline

Usage:
    python riley_run_one.py --symbol SPX [--date YYYY-MM-DD]

This script runs the full pipeline for a single instrument:
1. Load/ingest data
2. Compute pivots and levels
3. Generate charts
4. Write packet bundle
5. Generate skeleton report
6. Write DB records
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime
import pytz

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.database import Database
from riley.data import load_or_stub_data
from riley.features import (
    detect_pivots, rank_pivots, compute_volume_profile,
    compute_range_context, compute_volatility_regime, compute_trend_regime
)
from riley.packets import write_packets
from riley.reports import generate_skeleton_report
from riley.validate_v2 import validate_daily, validate_weekly
from riley.weekly_v2 import make_weekly_from_daily
from riley.charts_v2 import render_daily_weekly


def main():
    parser = argparse.ArgumentParser(description="Run Riley pipeline for one instrument")
    parser.add_argument('--symbol', required=True, help='Instrument symbol')
    parser.add_argument('--date', default=None, help='As-of date (YYYY-MM-DD), defaults to today Singapore time')
    parser.add_argument('--stub', action='store_true', help='Use stub data instead of IBKR (for testing)')
    parser.add_argument('--host', default='192.168.0.18', help='IBKR host address (default: 192.168.0.18)')
    parser.add_argument('--port', type=int, default=7496, help='IBKR port (default: 7496)')
    args = parser.parse_args()

    symbol = args.symbol

    # Determine as_of_date (Singapore timezone)
    if args.date:
        as_of_date = args.date
    else:
        sg_tz = pytz.timezone('Asia/Singapore')
        as_of_date = datetime.now(sg_tz).strftime('%Y-%m-%d')

    print(f"\n{'='*60}")
    print(f"Riley Pipeline - Single Instrument")
    print(f"Symbol: {symbol}")
    print(f"As-of Date: {as_of_date}")
    print(f"{'='*60}\n")

    # Initialize database
    db = Database()
    try:
        db.run_migrations()
        print("✓ Database migrations completed")
    except Exception as e:
        print(f"✗ Database migration failed: {e}")
        return 1

    # Create run record
    run_id = db.create_run(as_of_date)
    print(f"✓ Run ID: {run_id}")

    # Upsert instrument
    db.upsert_instrument(symbol, type_='equity', source_preference='STUB')
    print(f"✓ Instrument registered: {symbol}")

    try:
        # Step 1: Load data
        print(f"\n[1/6] Loading data for {symbol}...")
        if args.stub:
            print("Using stub data (--stub flag set)")
            df = load_or_stub_data(symbol, project_root, use_ibkr=False)
        else:
            print(f"Connecting to IBKR at {args.host}:{args.port}")
            df = load_or_stub_data(
                symbol, project_root,
                use_ibkr=True,
                host=args.host,
                port=args.port
            )
        print(f"✓ Loaded {len(df)} bars")

        # Validate daily data
        print("Validating daily data...")
        validate_daily(df)
        print("✓ Daily data validated")

        # Build weekly from daily
        print("Building weekly from daily...")
        df_weekly = make_weekly_from_daily(df)
        print(f"✓ Built {len(df_weekly)} weekly bars")

        # Validate weekly data
        print("Validating weekly data...")
        validate_weekly(df_weekly)
        print("✓ Weekly data validated")

        # Step 2: Compute features
        print(f"\n[2/6] Computing features...")

        pivots = detect_pivots(df, left=2, right=2)
        print(f"✓ Detected {len(pivots)} pivots")

        ranked_pivots = rank_pivots(pivots, df, top_n=10)
        print(f"✓ Ranked top {len(ranked_pivots)} pivots")

        vol_profile = compute_volume_profile(df)
        print(f"✓ Computed volume profile")

        range_context = compute_range_context(df)
        print(f"✓ Computed range context")

        volatility_regime = compute_volatility_regime(df)
        print(f"✓ Volatility regime: {volatility_regime['regime']}")

        trend_regime = compute_trend_regime(df)
        print(f"✓ Trend regime: {trend_regime['regime']}")

        # Step 3: Generate charts
        print(f"\n[3/6] Generating charts...")
        chart_dir = project_root / "artifacts" / "charts" / symbol / as_of_date
        levels_for_chart = {
            'poc_90td': vol_profile['poc_90td'],
            'poc_180td': vol_profile['poc_180td'],
            'poc_252td': vol_profile['poc_252td'],
            'range': range_context
        }
        render_daily_weekly(df, df_weekly, levels_for_chart, ranked_pivots, symbol, as_of_date, chart_dir)
        print(f"✓ Charts saved to {chart_dir}")

        # Step 4: Write packets
        print(f"\n[4/6] Writing packet bundle...")
        packet_dir = project_root / "artifacts" / "packets" / symbol / as_of_date

        # Check for cycle pack
        cycle_pack_path = project_root / "config" / "cycles" / f"{symbol}.yaml"
        cycle_pack = None
        if cycle_pack_path.exists():
            print(f"✓ Cycle pack found: {cycle_pack_path}")
            # TODO: load YAML when needed
        else:
            print(f"⚠ Cycle pack missing (expected at {cycle_pack_path})")

        packet_path = write_packets(
            symbol, as_of_date, df, ranked_pivots, vol_profile,
            range_context, volatility_regime, trend_regime,
            packet_dir, cycle_pack, data_quality=None
        )
        print(f"✓ Packet bundle written to {packet_dir}")

        # Step 5: Generate skeleton report
        print(f"\n[5/6] Generating skeleton report...")
        report_path = project_root / "reports" / "skeletons" / symbol / as_of_date / f"{symbol}_{as_of_date}_skeleton.md"
        generate_skeleton_report(symbol, as_of_date, packet_dir, report_path)
        print(f"✓ Skeleton report saved to {report_path}")

        # Step 6: Write DB records
        print(f"\n[6/6] Writing database records...")
        db.create_analysis(
            symbol=symbol,
            as_of_date=as_of_date,
            packet_path=str(packet_path),
            skeleton_report_path=str(report_path)
        )
        print(f"✓ Analysis record created")

        # Mark run as successful
        db.finish_run(run_id, 'success')

        print(f"\n{'='*60}")
        print(f"✓ Pipeline completed successfully for {symbol}")
        print(f"{'='*60}\n")

        return 0

    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        db.finish_run(run_id, 'failed')
        return 1

    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
