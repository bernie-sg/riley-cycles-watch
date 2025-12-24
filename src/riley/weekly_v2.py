"""Weekly aggregation from daily - no calendar spacing"""
import pandas as pd


def make_weekly_from_daily(df_daily: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily bars to weekly bars using ISO week grouping.

    Args:
        df_daily: Sanitized daily DataFrame with td_index and trading_date

    Returns:
        Weekly DataFrame with tw_index and week_end_label
    """
    if df_daily.empty:
        return pd.DataFrame()

    # Create working copy
    df = df_daily.copy()

    # Parse trading_date to datetime
    df['date'] = pd.to_datetime(df['trading_date'])

    # Extract ISO year and week
    df['iso_year'] = df['date'].dt.isocalendar().year
    df['iso_week'] = df['date'].dt.isocalendar().week

    # Group by ISO year/week
    grouped = df.groupby(['iso_year', 'iso_week'])

    # Build weekly bars
    weekly_data = []
    for (iso_year, iso_week), group in grouped:
        # Skip weeks with < 3 trading days
        if len(group) < 3:
            continue

        # Aggregate OHLCV
        week_bar = {
            'open': group['open'].iloc[0],
            'high': group['high'].max(),
            'low': group['low'].min(),
            'close': group['close'].iloc[-1],
            'volume': group['volume'].sum(),
            'week_end_label': group['trading_date'].iloc[-1],
            'iso_year': iso_year,
            'iso_week': iso_week,
            'bar_count': len(group)
        }

        # Skip weeks with zero volume
        if week_bar['volume'] <= 0:
            continue

        weekly_data.append(week_bar)

    # Create DataFrame
    df_weekly = pd.DataFrame(weekly_data)

    if df_weekly.empty:
        return df_weekly

    # Sort by ISO year/week
    df_weekly = df_weekly.sort_values(['iso_year', 'iso_week']).reset_index(drop=True)

    # Assign tw_index
    df_weekly['tw_index'] = range(len(df_weekly))

    # Select final columns
    df_weekly = df_weekly[['tw_index', 'open', 'high', 'low', 'close', 'volume', 'week_end_label']]

    return df_weekly
