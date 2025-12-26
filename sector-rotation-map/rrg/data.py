"""
Data loading and validation for RRG application
"""
import pandas as pd
import numpy as np
from typing import Tuple, Optional
from datetime import datetime


def detect_mode(df: pd.DataFrame) -> str:
    """
    Detect whether CSV contains precomputed metrics (Mode B) or raw OHLCV data (Mode A).

    Returns:
        'mode_a': Raw OHLCV data (needs computation)
        'mode_b': Precomputed rs_ratio and rs_momentum
    """
    required_mode_b = {'date', 'symbol', 'rs_ratio', 'rs_momentum'}
    required_mode_a = {'date', 'symbol', 'close'}

    cols = set(df.columns.str.lower())

    if required_mode_b.issubset(cols):
        return 'mode_b'
    elif required_mode_a.issubset(cols):
        return 'mode_a'
    else:
        raise ValueError(
            f"CSV must contain either:\n"
            f"Mode A: {required_mode_a}\n"
            f"Mode B: {required_mode_b}\n"
            f"Found: {cols}"
        )


def load_csv(file_path: str, mode: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
    """
    Load CSV and validate structure.

    Args:
        file_path: Path to CSV file
        mode: Force specific mode ('mode_a' or 'mode_b'), or None to auto-detect

    Returns:
        (DataFrame, mode_string)
    """
    df = pd.read_csv(file_path)

    # Normalize column names to lowercase
    df.columns = df.columns.str.lower().str.strip()

    # Detect mode if not specified
    if mode is None:
        mode = detect_mode(df)

    # Parse date column
    df['date'] = pd.to_datetime(df['date'])

    # Validate and clean
    df = df.dropna(subset=['date', 'symbol'])
    df['symbol'] = df['symbol'].str.upper().str.strip()

    # Sort by symbol and date
    df = df.sort_values(['symbol', 'date']).reset_index(drop=True)

    return df, mode


def validate_benchmark(df: pd.DataFrame, benchmark_symbol: str) -> bool:
    """
    Check if benchmark symbol exists in the data.

    Args:
        df: Data DataFrame
        benchmark_symbol: Benchmark ticker (e.g., 'SPY')

    Returns:
        True if benchmark found, False otherwise
    """
    return benchmark_symbol.upper() in df['symbol'].unique()


def filter_by_date(df: pd.DataFrame, end_date: Optional[str] = None, weeks_back: int = 5) -> pd.DataFrame:
    """
    Filter data to last N weeks ending on specified date.

    Args:
        df: Data DataFrame
        end_date: End date (YYYY-MM-DD) or None for latest
        weeks_back: Number of weeks to include

    Returns:
        Filtered DataFrame
    """
    if end_date is None:
        end_date = df['date'].max()
    else:
        end_date = pd.to_datetime(end_date)

    start_date = end_date - pd.Timedelta(weeks=weeks_back)

    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    return df[mask].copy()


def get_sector_universe(df: pd.DataFrame, universe: str = 'US_SECTORS') -> list:
    """
    Get list of symbols for specified universe.

    Args:
        df: Data DataFrame
        universe: Universe identifier

    Returns:
        List of symbols found in data
    """
    from .constants import US_SECTORS

    if universe == 'US_SECTORS':
        available_sectors = set(df['symbol'].unique())
        return [sym for sym in US_SECTORS.keys() if sym in available_sectors]
    else:
        # Return all non-benchmark symbols
        return sorted(df['symbol'].unique())


def get_latest_date(df: pd.DataFrame) -> str:
    """Get the latest date in the dataset as string."""
    return df['date'].max().strftime('%Y-%m-%d')


def get_date_range(df: pd.DataFrame) -> Tuple[str, str]:
    """Get the date range as (min_date, max_date) strings."""
    return (
        df['date'].min().strftime('%Y-%m-%d'),
        df['date'].max().strftime('%Y-%m-%d')
    )


def prepare_table_data(df: pd.DataFrame, mode: str, symbols: list, end_date: pd.Timestamp) -> pd.DataFrame:
    """
    Prepare data for display table.

    Args:
        df: Full DataFrame
        mode: 'mode_a' or 'mode_b'
        symbols: List of symbols to include
        end_date: Latest date for table

    Returns:
        DataFrame formatted for table display
    """
    from .constants import US_SECTORS

    # Get latest data point for each symbol
    latest = df[df['date'] == end_date].copy()
    latest = latest[latest['symbol'].isin(symbols)]

    # Build table
    table_data = []
    for _, row in latest.iterrows():
        symbol = row['symbol']
        record = {
            'Symbol': symbol,
            'Name': US_SECTORS.get(symbol, symbol),
            'Visible': True
        }

        if mode == 'mode_a' and 'close' in row:
            record['Price'] = f"${row['close']:.2f}"

            # Calculate % change if we have enough history
            symbol_data = df[df['symbol'] == symbol].sort_values('date')
            if len(symbol_data) >= 2:
                first_close = symbol_data.iloc[0]['close']
                last_close = row['close']
                pct_change = ((last_close / first_close) - 1) * 100
                record['% Change'] = f"{pct_change:+.2f}%"

        if mode == 'mode_b' or ('rs_ratio' in row and 'rs_momentum' in row):
            record['RS-Ratio'] = f"{row.get('rs_ratio', 0):.2f}"
            record['RS-Momentum'] = f"{row.get('rs_momentum', 0):.2f}"

        table_data.append(record)

    return pd.DataFrame(table_data)
