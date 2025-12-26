"""
RRG metric computations (Mode A)
"""
import pandas as pd
import numpy as np
from typing import Dict


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return series.rolling(window=period, min_periods=1).mean()


def compute_relative_strength(df: pd.DataFrame, benchmark_symbol: str = 'SPY') -> pd.DataFrame:
    """
    Compute relative strength for all symbols vs benchmark.

    Args:
        df: DataFrame with columns [date, symbol, close]
        benchmark_symbol: Benchmark ticker

    Returns:
        DataFrame with RS column added
    """
    # Get benchmark prices
    benchmark = df[df['symbol'] == benchmark_symbol][['date', 'close']].rename(
        columns={'close': 'benchmark_close'}
    )

    # Merge benchmark with all symbols
    result = df.merge(benchmark, on='date', how='left')

    # Calculate RS = close / benchmark_close
    result['rs'] = result['close'] / result['benchmark_close']

    # Fill any NaN values forward (in case benchmark has gaps)
    result['rs'] = result.groupby('symbol')['rs'].fillna(method='ffill')

    return result


def compute_rrg_metrics(
    df: pd.DataFrame,
    benchmark_symbol: str = 'SPY',
    rs_smoothing: int = 10,
    ratio_lookback: int = 10,
    momentum_lookback: int = 10
) -> pd.DataFrame:
    """
    Compute full RRG metrics (RS-Ratio and RS-Momentum).

    Args:
        df: DataFrame with columns [date, symbol, close]
        benchmark_symbol: Benchmark ticker
        rs_smoothing: EMA period for RS smoothing
        ratio_lookback: Rolling mean period for RS-Ratio
        momentum_lookback: Rolling mean period for RS-Momentum

    Returns:
        DataFrame with rs_ratio and rs_momentum columns
    """
    # Step 1: Calculate raw relative strength
    df = compute_relative_strength(df, benchmark_symbol)

    results = []

    for symbol in df['symbol'].unique():
        if symbol == benchmark_symbol:
            continue  # Skip benchmark itself

        symbol_data = df[df['symbol'] == symbol].copy().sort_values('date')

        # Step 2: Smooth RS with EMA
        symbol_data['rs_smooth'] = calculate_ema(symbol_data['rs'], rs_smoothing)

        # Step 3: Calculate RS-Ratio
        # RS-Ratio = 100 * (smoothed_rs / rolling_mean_of_smoothed_rs)
        rs_smooth_mean = calculate_sma(symbol_data['rs_smooth'], ratio_lookback)
        symbol_data['rs_ratio'] = 100 * (symbol_data['rs_smooth'] / rs_smooth_mean)

        # Step 4: Calculate RS-Momentum
        # RS-Momentum = 100 * (rs_ratio / rolling_mean_of_rs_ratio)
        rs_ratio_mean = calculate_sma(symbol_data['rs_ratio'], momentum_lookback)
        symbol_data['rs_momentum'] = 100 * (symbol_data['rs_ratio'] / rs_ratio_mean)

        results.append(symbol_data)

    # Combine all symbols
    final_df = pd.concat(results, ignore_index=True)

    # Fill any inf/nan values with 100 (neutral)
    final_df['rs_ratio'] = final_df['rs_ratio'].replace([np.inf, -np.inf], np.nan).fillna(100)
    final_df['rs_momentum'] = final_df['rs_momentum'].replace([np.inf, -np.inf], np.nan).fillna(100)

    return final_df


def get_tail_coordinates(df: pd.DataFrame, symbol: str, end_date: pd.Timestamp, tail_weeks: int = 5) -> Dict:
    """
    Get coordinates for drawing the tail (historical path).

    Args:
        df: DataFrame with rs_ratio and rs_momentum
        symbol: Symbol to get tail for
        end_date: Latest date (tail endpoint)
        tail_weeks: Number of weeks to include in tail

    Returns:
        Dict with x, y coordinates and dates
    """
    # Filter to symbol and date range
    start_date = end_date - pd.Timedelta(weeks=tail_weeks)
    mask = (df['symbol'] == symbol) & (df['date'] >= start_date) & (df['date'] <= end_date)
    tail_data = df[mask].sort_values('date')

    if tail_data.empty:
        return {'x': [], 'y': [], 'dates': []}

    return {
        'x': tail_data['rs_ratio'].tolist(),
        'y': tail_data['rs_momentum'].tolist(),
        'dates': tail_data['date'].dt.strftime('%Y-%m-%d').tolist()
    }


def get_latest_point(df: pd.DataFrame, symbol: str, end_date: pd.Timestamp) -> Dict:
    """
    Get the latest point coordinates for a symbol.

    Args:
        df: DataFrame with rs_ratio and rs_momentum
        symbol: Symbol to get point for
        end_date: Date for latest point

    Returns:
        Dict with x, y coordinates
    """
    point = df[(df['symbol'] == symbol) & (df['date'] == end_date)]

    if point.empty:
        return {'x': None, 'y': None}

    return {
        'x': point['rs_ratio'].iloc[0],
        'y': point['rs_momentum'].iloc[0]
    }


def calculate_percent_change(df: pd.DataFrame, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp) -> float:
    """
    Calculate percent price change for a symbol over a date range.

    Args:
        df: DataFrame with close prices
        symbol: Symbol to calculate for
        start_date: Start date
        end_date: End date

    Returns:
        Percent change as float
    """
    symbol_data = df[df['symbol'] == symbol].sort_values('date')

    # Get closes at start and end
    start_close = symbol_data[symbol_data['date'] <= start_date]['close'].iloc[-1] if len(
        symbol_data[symbol_data['date'] <= start_date]) > 0 else None
    end_close = symbol_data[symbol_data['date'] <= end_date]['close'].iloc[-1] if len(
        symbol_data[symbol_data['date'] <= end_date]) > 0 else None

    if start_close is None or end_close is None or start_close == 0:
        return 0.0

    return ((end_close / start_close) - 1) * 100
