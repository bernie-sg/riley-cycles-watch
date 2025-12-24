#!/usr/bin/env python3
"""
Riley Project - Backfill ES History from TradingView

This script:
1. Loads TradingView history bars from a folder
2. Sanitizes data (strict quality checks)
3. Merges with existing IBKR data
4. Aggregates to weekly with quality filters
5. Writes unified datasets (daily + weekly)

Usage:
    python riley_backfill_es_from_tv.py --folder "history bars"
    python riley_backfill_es_from_tv.py --folder "history bars" --symbol ES
"""
import sys
import argparse
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.data import load_tradingview_history_folder, sanitize_bars
from riley.merge import merge_tradingview_with_ibkr, aggregate_to_weekly
import pandas as pd
from datetime import datetime
import pytz


def main():
    parser = argparse.ArgumentParser(description="Backfill ES history from TradingView CSV")
    parser.add_argument('--folder', default='history bars', help='Folder containing TradingView CSV files')
    parser.add_argument('--symbol', default='ES', help='Instrument symbol (default: ES)')
    args = parser.parse_args()

    symbol = args.symbol
    folder_path = project_root / args.folder

    # Get as_of_date for logging
    sg_tz = pytz.timezone('Asia/Singapore')
    as_of_date = datetime.now(sg_tz).strftime('%Y-%m-%d')

    print(f"\n{'='*60}")
    print(f"Riley Project - TradingView Backfill")
    print(f"Symbol: {symbol}")
    print(f"Folder: {folder_path}")
    print(f"As-of: {as_of_date}")
    print(f"{'='*60}\n")

    # Step 1: Load TradingView history
    print("[1/6] Loading TradingView history from folder...")
    try:
        tv_df = load_tradingview_history_folder(str(folder_path), symbol=symbol)
        tv_rows = len(tv_df)
        print(f"✓ TradingView: {tv_rows} bars loaded\n")
    except Exception as e:
        print(f"✗ Failed to load TradingView data: {e}")
        return 1

    # Step 2: Sanitize TradingView data
    print("[2/6] Sanitizing TradingView data...")
    try:
        tv_df, tv_quality = sanitize_bars(tv_df, symbol, f"{as_of_date}_tv", project_root)
        print()
    except Exception as e:
        print(f"✗ Sanitation failed: {e}")
        return 1

    # Step 3: Load existing IBKR data (if available)
    print("[3/6] Loading existing IBKR data (if available)...")
    ibkr_raw_path = project_root / "data" / "raw" / "ibkr" / symbol / "D.csv"
    ibkr_processed_path = project_root / "data" / "processed" / symbol / "D.parquet"

    ibkr_df = pd.DataFrame()
    ibkr_rows = 0

    # Try processed first, fall back to raw
    if ibkr_processed_path.exists():
        try:
            ibkr_df = pd.read_parquet(ibkr_processed_path)
            ibkr_rows = len(ibkr_df)
            print(f"✓ IBKR: {ibkr_rows} bars loaded from processed")
        except Exception as e:
            print(f"Warning: Could not load IBKR processed data: {e}")

    elif ibkr_raw_path.exists():
        try:
            ibkr_df = pd.read_csv(ibkr_raw_path)
            ibkr_df['timestamp'] = pd.to_datetime(ibkr_df['timestamp'], utc=True)
            ibkr_rows = len(ibkr_df)
            print(f"✓ IBKR: {ibkr_rows} bars loaded from raw")
        except Exception as e:
            print(f"Warning: Could not load IBKR raw data: {e}")
    else:
        print("No existing IBKR data found (fresh start)")

    # Sanitize IBKR data if not empty
    if not ibkr_df.empty:
        print("\nSanitizing IBKR data...")
        try:
            ibkr_df, ibkr_quality = sanitize_bars(ibkr_df, symbol, f"{as_of_date}_ibkr", project_root)
        except Exception as e:
            print(f"✗ IBKR sanitation failed: {e}")
            return 1

    print()

    # Step 4: Merge datasets
    print("[4/6] Merging TradingView and IBKR data...")
    merged_daily = merge_tradingview_with_ibkr(tv_df, ibkr_df)
    merged_rows = len(merged_daily)
    print()

    # Step 5: Write outputs
    print("[5/6] Writing unified datasets...")

    # Write TradingView raw data
    tv_raw_path = project_root / "data" / "raw" / "tradingview" / symbol / "D.csv"
    tv_raw_path.parent.mkdir(parents=True, exist_ok=True)
    tv_df.to_csv(tv_raw_path, index=False)
    print(f"✓ Written: {tv_raw_path}")

    # Write merged daily processed data
    daily_processed_path = project_root / "data" / "processed" / symbol / "D.parquet"
    daily_processed_path.parent.mkdir(parents=True, exist_ok=True)
    merged_daily.to_parquet(daily_processed_path)
    print(f"✓ Written: {daily_processed_path}")

    # Step 6: Aggregate to weekly
    print("\n[6/6] Aggregating to weekly...")
    weekly_df = aggregate_to_weekly(merged_daily)
    weekly_rows = len(weekly_df)

    # Write weekly processed data
    weekly_processed_path = project_root / "data" / "processed" / symbol / "W.parquet"
    weekly_df.to_parquet(weekly_processed_path)
    print(f"✓ Written: {weekly_processed_path}")

    # Calculate statistics
    overlap_count = tv_rows + ibkr_rows - merged_rows
    date_start = merged_daily['timestamp'].min()
    date_end = merged_daily['timestamp'].max()

    # Summary
    print(f"\n{'='*60}")
    print("BACKFILL SUMMARY")
    print(f"{'='*60}")
    print(f"TradingView rows ingested: {tv_rows}")
    print(f"IBKR rows loaded: {ibkr_rows}")
    print(f"Overlap count: {overlap_count}")
    print(f"Final unified rows (daily): {merged_rows}")
    print(f"Final unified rows (weekly): {weekly_rows}")
    print(f"Final date range: {date_start.date()} → {date_end.date()}")
    print(f"\nPaths written:")
    print(f"  - {tv_raw_path}")
    print(f"  - {daily_processed_path}")
    print(f"  - {weekly_processed_path}")
    print(f"{'='*60}\n")

    print("✓ Backfill completed successfully")
    print("\nNext: Run pipeline to regenerate charts with extended history:")
    print(f"  python3 scripts/riley_run_one.py --symbol {symbol} --host 192.168.0.18 --port 7496")

    return 0


if __name__ == '__main__':
    sys.exit(main())
