"""Data validation for charting pipeline - fail hard if bad data"""
import pandas as pd
import numpy as np


def validate_daily(df_daily: pd.DataFrame) -> None:
    """
    Validate daily data before charting.

    Raises:
        ValueError: If validation fails
    """
    # Check td_index exists
    if 'td_index' not in df_daily.columns:
        raise ValueError("Daily data missing td_index column")

    # Check td_index is monotonic and starts at 0
    if not df_daily['td_index'].is_monotonic_increasing:
        raise ValueError("Daily td_index is not monotonic increasing")

    if df_daily['td_index'].iloc[0] != 0:
        raise ValueError(f"Daily td_index must start at 0, got {df_daily['td_index'].iloc[0]}")

    # Check required columns exist
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df_daily.columns:
            raise ValueError(f"Daily data missing {col} column")

    # Check for NaN in OHLCV
    if df_daily[required_cols].isna().any().any():
        raise ValueError("Daily data contains NaN values in OHLCV")

    # Check price validity
    if (df_daily['low'] <= 0).any():
        raise ValueError("Daily data contains low <= 0")

    if (df_daily['high'] <= 0).any():
        raise ValueError("Daily data contains high <= 0")

    if (df_daily['low'] > df_daily['high']).any():
        raise ValueError("Daily data contains low > high")

    # Check for absurd returns in visible window (last 252 bars)
    window_df = df_daily.tail(252)
    if len(window_df) > 1:
        returns = np.log(window_df['close'] / window_df['close'].shift(1))
        if (np.abs(returns) > 0.25).any():
            raise ValueError("Daily data contains absurd returns (>25%) in visible window")


def validate_weekly(df_weekly: pd.DataFrame) -> None:
    """
    Validate weekly data before charting.

    Raises:
        ValueError: If validation fails
    """
    # Check tw_index exists
    if 'tw_index' not in df_weekly.columns:
        raise ValueError("Weekly data missing tw_index column")

    # Check tw_index is monotonic and starts at 0
    if not df_weekly['tw_index'].is_monotonic_increasing:
        raise ValueError("Weekly tw_index is not monotonic increasing")

    if df_weekly['tw_index'].iloc[0] != 0:
        raise ValueError(f"Weekly tw_index must start at 0, got {df_weekly['tw_index'].iloc[0]}")

    # Check required columns exist
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in required_cols:
        if col not in df_weekly.columns:
            raise ValueError(f"Weekly data missing {col} column")

    # Check for NaN in OHLCV
    if df_weekly[required_cols].isna().any().any():
        raise ValueError("Weekly data contains NaN values in OHLCV")

    # Check price validity
    if (df_weekly['low'] <= 0).any():
        raise ValueError("Weekly data contains low <= 0")

    if (df_weekly['high'] <= 0).any():
        raise ValueError("Weekly data contains high <= 0")

    if (df_weekly['low'] > df_weekly['high']).any():
        raise ValueError("Weekly data contains low > high")
