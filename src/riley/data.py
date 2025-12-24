"""Data loading and ingestion for Riley Project"""
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
import pytz


def load_or_stub_data(symbol: str, project_root: Path, use_ibkr: bool = True,
                      host: str = None, port: int = None) -> pd.DataFrame:
    """
    Load data for symbol from IBKR with append-only logic.

    Args:
        symbol: Instrument symbol (ES or SPX)
        project_root: Project root path
        use_ibkr: If True, fetch from IBKR; if False, use stub (for testing)
        host: IBKR host (defaults to 192.168.0.18)
        port: IBKR port (defaults to 7496)

    Returns:
        DataFrame with daily bars

    Process:
        1. Check if processed data exists
        2. If exists, load and find max timestamp
        3. Fetch only new bars from IBKR (append-only)
        4. Merge with existing data
        5. Deduplicate on timestamp
        6. Save to raw (append) and processed (overwrite)
    """
    from riley.ibkr import fetch_ibkr_historical_bars

    processed_path = project_root / "data" / "processed" / symbol / "D.parquet"
    raw_path = project_root / "data" / "raw" / "ibkr" / symbol / "D.csv"

    # Check if processed data exists
    if processed_path.exists():
        print(f"Loading existing data from {processed_path}")
        existing_df = pd.read_parquet(processed_path)
        existing_df['timestamp'] = pd.to_datetime(existing_df['timestamp'], utc=True)

        # Find the latest timestamp
        max_timestamp = existing_df['timestamp'].max()
        print(f"Existing data: {len(existing_df)} bars, latest: {max_timestamp.date()}")

        if not use_ibkr:
            print("[STUB MODE] Returning existing data without fetching new bars")
            return existing_df

        # Fetch only new bars (after max timestamp)
        end_date = datetime.now(timezone.utc)
        start_date = max_timestamp + pd.Timedelta(days=1)

        if start_date >= end_date:
            print("✓ Data is up to date, no new bars to fetch")
            return existing_df

        print(f"Fetching new bars from {start_date.date()} to {end_date.date()}")

        try:
            new_df = fetch_ibkr_historical_bars(
                symbol=symbol,
                timeframe="D",
                start_date=start_date,
                end_date=end_date,
                host=host,
                port=port
            )

            if len(new_df) == 0:
                print("No new bars returned from IBKR")
                return existing_df

            print(f"✓ Fetched {len(new_df)} new bars")

            # Append to raw CSV
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            _append_to_raw_csv(new_df, raw_path, symbol)

            # Merge with existing data
            merged_df = pd.concat([existing_df, new_df], ignore_index=True)

            # Deduplicate on timestamp (keep last)
            merged_df = merged_df.drop_duplicates(subset=['timestamp'], keep='last')
            merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)

            print(f"✓ Total bars after merge: {len(merged_df)}")

            # Save processed data
            processed_path.parent.mkdir(parents=True, exist_ok=True)
            merged_df.to_parquet(processed_path)

            return merged_df

        except Exception as e:
            print(f"✗ Failed to fetch new bars: {e}")
            print("Returning existing data")
            return existing_df

    else:
        # No existing data - fetch full history
        print(f"No existing data for {symbol}")

        if not use_ibkr:
            print("[STUB MODE] Generating sample data")
            return _generate_stub_data(symbol, processed_path)

        print("Fetching full history from IBKR")

        try:
            end_date = datetime.now(timezone.utc)
            df = fetch_ibkr_historical_bars(
                symbol=symbol,
                timeframe="D",
                start_date=None,  # Fetch max history
                end_date=end_date,
                host=host,
                port=port
            )

            print(f"✓ Fetched {len(df)} bars")

            # Add metadata
            df['symbol'] = symbol
            df['source'] = 'IBKR'
            df['timeframe'] = 'D'

            # Save to raw CSV
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            _append_to_raw_csv(df, raw_path, symbol)

            # Save to processed parquet
            processed_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(processed_path)

            return df

        except Exception as e:
            print(f"✗ Failed to fetch data from IBKR: {e}")
            raise RuntimeError(f"Cannot load data for {symbol} and IBKR fetch failed: {e}")


def _append_to_raw_csv(df: pd.DataFrame, raw_path: Path, symbol: str):
    """
    Append bars to raw CSV (append-only).

    If file exists, append. If not, create with header.
    """
    df_to_save = df.copy()
    df_to_save['symbol'] = symbol
    df_to_save['source'] = 'IBKR'
    df_to_save['timeframe'] = 'D'

    if raw_path.exists():
        # Append mode
        df_to_save.to_csv(raw_path, mode='a', header=False, index=False)
        print(f"✓ Appended {len(df_to_save)} bars to {raw_path}")
    else:
        # Create new
        df_to_save.to_csv(raw_path, mode='w', header=True, index=False)
        print(f"✓ Created raw CSV with {len(df_to_save)} bars at {raw_path}")


def _generate_stub_data(symbol: str, processed_path: Path) -> pd.DataFrame:
    """
    Generate stub data for testing (fallback only).
    """
    print(f"[STUB] Generating sample data for {symbol}")
    dates = pd.date_range(end=datetime.now(), periods=500, freq='D', tz='UTC')

    import numpy as np
    np.random.seed(hash(symbol) % 2**32)
    returns = np.random.randn(500) * 0.02
    prices = 100 * (1 + returns).cumprod()

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * (1 + np.random.randn(500) * 0.005),
        'high': prices * (1 + np.abs(np.random.randn(500)) * 0.01),
        'low': prices * (1 - np.abs(np.random.randn(500)) * 0.01),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 500),
        'symbol': symbol,
        'source': 'STUB',
        'timeframe': 'D'
    })

    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(processed_path)

    return df


def ingest_tradingview_csv(csv_path: str, symbol: str, project_root: Path) -> pd.DataFrame:
    """
    Ingest TradingView CSV and standardize to schema.

    Expected CSV format: time,open,high,low,close,volume
    """
    df = pd.read_csv(csv_path)

    # Standardize column names
    column_map = {
        'time': 'timestamp',
        'Time': 'timestamp'
    }
    df.rename(columns=column_map, inplace=True)

    # Convert timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Add metadata
    df['symbol'] = symbol
    df['source'] = 'TRADINGVIEW'
    df['timeframe'] = 'D'

    # Ensure required columns
    required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Save to processed
    output_path = project_root / "data" / "processed" / symbol / "D.parquet"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path)

    return df


def load_tradingview_history_folder(folder_path: str, symbol: str = 'ES') -> pd.DataFrame:
    """
    Load TradingView history bars from a folder containing CSV exports.

    Supports multiple CSV/TXT files and various TradingView export formats:
    - Columns: time/Time, open/Open, high/High, low/Low, close/Close, volume/Volume
    - Timestamps: UNIX seconds, UNIX milliseconds, or ISO strings

    Args:
        folder_path: Path to folder containing TradingView CSV exports
        symbol: Instrument symbol (default: ES)

    Returns:
        DataFrame with standardized schema, sorted by timestamp ascending
    """
    from glob import glob
    import os

    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    # Find all CSV and TXT files
    csv_files = list(folder.glob('*.csv')) + list(folder.glob('*.txt'))

    if not csv_files:
        raise FileNotFoundError(f"No CSV/TXT files found in {folder_path}")

    print(f"Found {len(csv_files)} file(s) in {folder_path}")

    all_data = []

    for csv_file in csv_files:
        print(f"Loading {csv_file.name}...")
        df = pd.read_csv(csv_file)

        # Standardize column names (handle various TradingView formats)
        column_map = {
            'time': 'timestamp',
            'Time': 'timestamp',
            'Date': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'vol': 'volume'
        }
        df.rename(columns=column_map, inplace=True)

        # Convert timestamp to datetime (handle UNIX seconds, ms, or ISO strings)
        if 'timestamp' not in df.columns:
            raise ValueError(f"No timestamp column found in {csv_file.name}")

        # Detect timestamp format
        sample_ts = df['timestamp'].iloc[0]

        if isinstance(sample_ts, str):
            # ISO string or date string
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
        elif sample_ts > 1e10:
            # UNIX milliseconds
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        else:
            # UNIX seconds
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)

        # Ensure required columns exist
        required = ['timestamp', 'open', 'high', 'low', 'close']
        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}' in {csv_file.name}")

        # Handle missing volume (some exports don't include it)
        if 'volume' not in df.columns:
            print(f"  Warning: No volume column, setting to 0")
            df['volume'] = 0

        # Select only required columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        all_data.append(df)
        print(f"  Loaded {len(df)} bars from {csv_file.name}")

    # Concatenate all files
    combined_df = pd.concat(all_data, ignore_index=True)

    # Sort by timestamp
    combined_df = combined_df.sort_values('timestamp').reset_index(drop=True)

    # Remove duplicates (keep first occurrence)
    initial_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['timestamp'], keep='first')
    dupes_removed = initial_count - len(combined_df)

    if dupes_removed > 0:
        print(f"Removed {dupes_removed} duplicate timestamps")

    # Add metadata
    combined_df['symbol'] = symbol
    combined_df['source'] = 'TRADINGVIEW'
    combined_df['timeframe'] = 'D'

    print(f"Total bars loaded: {len(combined_df)}")
    print(f"Date range: {combined_df['timestamp'].min()} to {combined_df['timestamp'].max()}")

    return combined_df


def sanitize_bars(df: pd.DataFrame, symbol: str, as_of_date: str,
                  project_root: Path = None) -> tuple[pd.DataFrame, dict]:
    """
    Strict data validation and sanitation.

    Drops bars with:
    - low <= 0 or high <= 0
    - low > high
    - abs(log(close / prev_close)) > 0.25
    - low < 0.5 * rolling_median(close, 252)
    - high > 2.0 * rolling_median(close, 252)
    - NaN in OHLCV

    Returns:
        (sanitized_df, quality_report)
    """
    import numpy as np

    initial_count = len(df)
    df = df.copy()

    quality_report = {
        'bars_dropped': 0,
        'drop_pct': 0.0,
        'reasons': {
            'bad_price': 0,
            'outlier_return': 0,
            'nan_ohlcv': 0,
            'extreme_outlier': 0
        }
    }

    # Drop NaN in OHLCV
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    before = len(df)
    df = df.dropna(subset=required_cols)
    dropped_nan = before - len(df)
    quality_report['reasons']['nan_ohlcv'] = dropped_nan

    # Drop bad prices
    bad_price_mask = (df['low'] <= 0) | (df['high'] <= 0) | (df['low'] > df['high'])
    dropped_bad_price = bad_price_mask.sum()
    df = df[~bad_price_mask]
    quality_report['reasons']['bad_price'] = dropped_bad_price

    # Sort by timestamp for sequential checks
    df = df.sort_values('timestamp').reset_index(drop=True)

    # Compute rolling median for outlier detection
    df['rolling_median_close'] = df['close'].rolling(window=min(252, len(df)), center=True, min_periods=1).median()

    # Drop extreme outliers (low < 0.5 * median or high > 2.0 * median)
    extreme_outlier_mask = (df['low'] < 0.5 * df['rolling_median_close']) | \
                           (df['high'] > 2.0 * df['rolling_median_close'])
    dropped_extreme = extreme_outlier_mask.sum()
    df = df[~extreme_outlier_mask]
    quality_report['reasons']['extreme_outlier'] = dropped_extreme

    # Re-sort after dropping extreme outliers
    df = df.sort_values('timestamp').reset_index(drop=True)

    # Drop outlier returns (abs(log(close/prev_close)) > 0.25)
    df['prev_close'] = df['close'].shift(1)
    df['log_return'] = np.log(df['close'] / df['prev_close'])
    outlier_return_mask = df['log_return'].abs() > 0.25
    dropped_outlier_return = outlier_return_mask.sum()
    df = df[~outlier_return_mask]
    quality_report['reasons']['outlier_return'] = dropped_outlier_return

    # Clean up helper columns
    df = df.drop(columns=['rolling_median_close', 'prev_close', 'log_return'])

    # Calculate summary
    final_count = len(df)
    total_dropped = initial_count - final_count
    quality_report['bars_dropped'] = total_dropped
    quality_report['drop_pct'] = (total_dropped / initial_count * 100) if initial_count > 0 else 0.0

    # Log to file
    if project_root and total_dropped > 0:
        log_dir = project_root / "logs" / "data_quality"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{symbol}_{as_of_date}.log"

        with open(log_path, 'w') as f:
            f.write(f"Data Quality Report - {symbol} - {as_of_date}\n")
            f.write(f"{'='*60}\n")
            f.write(f"Initial bars: {initial_count}\n")
            f.write(f"Final bars: {final_count}\n")
            f.write(f"Dropped: {total_dropped} ({quality_report['drop_pct']:.2f}%)\n")
            f.write(f"\nReasons:\n")
            for reason, count in quality_report['reasons'].items():
                f.write(f"  {reason}: {count}\n")

        print(f"✓ Data quality log: {log_path}")

    # Fail if >0.5% dropped
    if quality_report['drop_pct'] > 0.5:
        raise RuntimeError(
            f"Data quality failure: {quality_report['drop_pct']:.2f}% bars dropped (threshold: 0.5%)\n"
            f"Reasons: {quality_report['reasons']}"
        )

    print(f"✓ Sanitation: {total_dropped} bars dropped ({quality_report['drop_pct']:.4f}%)")

    return df, quality_report
