"""Data merging logic for Riley Project"""
import pandas as pd
from pathlib import Path


def merge_tradingview_with_ibkr(tv_df: pd.DataFrame, ibkr_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge TradingView and IBKR data with intelligent deduplication by trading DATE.

    Merge preference rule:
    - Compare by trading DATE, not exact timestamp (handles different UTC offsets)
    - When trading days overlap, prefer IBKR (more reliable exchange feed)
    - Exception: If IBKR volume is 0/missing and TradingView has volume, use TradingView volume
    - Never average prices

    Args:
        tv_df: TradingView DataFrame with standard schema
        ibkr_df: IBKR DataFrame with standard schema

    Returns:
        Merged DataFrame with longest possible history, deduplicated by trading date
    """
    if tv_df.empty:
        print("TradingView data is empty, using IBKR only")
        return ibkr_df

    if ibkr_df.empty:
        print("IBKR data is empty, using TradingView only")
        return tv_df

    # Ensure timestamps are datetime and timezone-aware
    tv_df = tv_df.copy()
    ibkr_df = ibkr_df.copy()
    tv_df['timestamp'] = pd.to_datetime(tv_df['timestamp'], utc=True)
    ibkr_df['timestamp'] = pd.to_datetime(ibkr_df['timestamp'], utc=True)

    # Add trading date column (date in UTC)
    tv_df['trading_date'] = tv_df['timestamp'].dt.date
    ibkr_df['trading_date'] = ibkr_df['timestamp'].dt.date

    # Find overlapping trading DATES
    tv_dates = set(tv_df['trading_date'])
    ibkr_dates = set(ibkr_df['trading_date'])
    overlap_dates = tv_dates & ibkr_dates

    overlap_count = len(overlap_dates)
    print(f"Overlap: {overlap_count} trading dates exist in both datasets")

    # Separate non-overlapping data
    tv_only = tv_df[~tv_df['trading_date'].isin(overlap_dates)].copy()
    ibkr_only = ibkr_df[~ibkr_df['trading_date'].isin(overlap_dates)].copy()

    print(f"TradingView-only bars: {len(tv_only)}")
    print(f"IBKR-only bars: {len(ibkr_only)}")

    # Handle overlapping bars with preference rules
    if overlap_count > 0:
        overlapping_ibkr = ibkr_df[ibkr_df['trading_date'].isin(overlap_dates)].copy()
        overlapping_tv = tv_df[tv_df['trading_date'].isin(overlap_dates)].copy()

        # Merge on trading_date to align rows
        merged_overlap = overlapping_ibkr.merge(
            overlapping_tv[['trading_date', 'volume']],
            on='trading_date',
            how='left',
            suffixes=('', '_tv')
        )

        # Apply volume preference rule:
        # If IBKR volume is 0 or NaN, use TradingView volume
        merged_overlap['volume'] = merged_overlap.apply(
            lambda row: row['volume_tv'] if (pd.isna(row['volume']) or row['volume'] == 0) and row['volume_tv'] > 0 else row['volume'],
            axis=1
        )

        # Drop the TV volume column
        merged_overlap = merged_overlap.drop(columns=['volume_tv'])

        print(f"Resolved {overlap_count} overlapping trading dates (preferring IBKR with volume fallback)")
    else:
        merged_overlap = pd.DataFrame()

    # Combine all datasets
    combined = pd.concat([tv_only, ibkr_only, merged_overlap], ignore_index=True)

    # Drop trading_date helper column
    combined = combined.drop(columns=['trading_date'])

    # Sort by timestamp
    combined = combined.sort_values('timestamp').reset_index(drop=True)

    # Final deduplication by date (safety check)
    combined['date_check'] = combined['timestamp'].dt.date
    before = len(combined)
    combined = combined.drop_duplicates(subset=['date_check'], keep='first')
    combined = combined.drop(columns=['date_check'])
    after = len(combined)

    if before != after:
        print(f"Warning: Removed {before - after} duplicate dates in final dataset")

    # Add trading day index (canonical timebase)
    combined['td_index'] = range(len(combined))

    # Add trading_date label for display (derived from timestamp)
    combined['trading_date'] = combined['timestamp'].dt.strftime('%Y-%m-%d')

    print(f"Final merged dataset: {len(combined)} bars (td_index: 0-{len(combined)-1})")

    return combined


def aggregate_to_weekly(daily_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily bars to weekly bars with strict quality rules.

    Weekly bars end on Friday:
    - Open = first day's open
    - High = max high
    - Low = min low
    - Close = last day's close
    - Volume = sum of volumes
    - source = "MERGED" if mixed sources, else preserve
    - symbol = preserve from daily

    Quality rules:
    - Drop weeks with <3 trading days
    - Drop weeks with zero total volume
    - Ensure exactly ONE candle per week
    - No NaN OHLC allowed post-aggregation

    Args:
        daily_df: Daily bars DataFrame

    Returns:
        Weekly bars DataFrame
    """
    if daily_df.empty:
        return daily_df

    df = daily_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

    # Preserve metadata
    symbol = df['symbol'].iloc[0] if 'symbol' in df.columns else 'UNKNOWN'
    sources = df['source'].unique() if 'source' in df.columns else ['UNKNOWN']
    source = 'MERGED' if len(sources) > 1 else sources[0]

    # Set timestamp as index for resampling
    df.set_index('timestamp', inplace=True)

    # Resample to weekly (W-FRI = week ending Friday)
    weekly = pd.DataFrame()
    weekly['open'] = df['open'].resample('W-FRI').first()
    weekly['high'] = df['high'].resample('W-FRI').max()
    weekly['low'] = df['low'].resample('W-FRI').min()
    weekly['close'] = df['close'].resample('W-FRI').last()
    weekly['volume'] = df['volume'].resample('W-FRI').sum()
    weekly['bar_count'] = df['close'].resample('W-FRI').count()  # Track days per week

    # Reset index to make timestamp a column
    weekly.reset_index(inplace=True)

    before_quality_filter = len(weekly)

    # Drop rows with NaN (incomplete weeks)
    weekly = weekly.dropna(subset=['open', 'high', 'low', 'close'])

    # Drop weeks with <3 trading days
    weekly = weekly[weekly['bar_count'] >= 3]

    # Drop weeks with zero total volume
    weekly = weekly[weekly['volume'] > 0]

    # Drop helper column
    weekly = weekly.drop(columns=['bar_count'])

    after_quality_filter = len(weekly)
    dropped_weeks = before_quality_filter - after_quality_filter

    if dropped_weeks > 0:
        print(f"Dropped {dropped_weeks} partial/invalid weeks (<3 days or zero volume)")

    # Add metadata
    weekly['symbol'] = symbol
    weekly['source'] = source
    weekly['timeframe'] = 'W'

    # Add trading week index (canonical timebase)
    weekly['tw_index'] = range(len(weekly))

    # Add week_end_date label for display (derived from timestamp)
    weekly['week_end_date'] = weekly['timestamp'].dt.strftime('%Y-%m-%d')

    print(f"Aggregated {len(df)} daily bars to {len(weekly)} weekly bars (tw_index: 0-{len(weekly)-1})")

    return weekly
