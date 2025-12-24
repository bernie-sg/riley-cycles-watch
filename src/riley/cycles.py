"""Cycle window resolution for Riley Project - Bar Index Based Only"""
import pandas as pd
from typing import Dict, Optional, Any


def resolve_daily_cycle_window(
    df_daily: pd.DataFrame,
    anchor_td_index: int,
    length_td: int,
    tol_td: int = 5
) -> Dict[str, Any]:
    """
    Resolve a daily cycle window using trading-bar indices only.

    NO calendar arithmetic. Only bar-index ranges.

    Args:
        df_daily: Daily dataframe with td_index column
        anchor_td_index: Anchor point (trading day index)
        length_td: Cycle length in trading days
        tol_td: Tolerance window in trading days (default 5TD)

    Returns:
        Dict with:
        - start_td_index: int
        - end_td_index: int
        - anchor_td_index: int
        - length_td: int
        - start_date_label: str (YYYY-MM-DD) for display only
        - end_date_label: str (YYYY-MM-DD) for display only
        - anchor_date_label: str (YYYY-MM-DD) for display only
    """
    if 'td_index' not in df_daily.columns:
        raise ValueError("DataFrame must have td_index column")

    max_td = df_daily['td_index'].max()

    # Validate anchor
    if anchor_td_index < 0 or anchor_td_index > max_td:
        raise ValueError(f"anchor_td_index {anchor_td_index} out of range [0, {max_td}]")

    # Calculate window bounds (pure bar-index arithmetic)
    start_td = max(0, anchor_td_index - length_td - tol_td)
    end_td = min(max_td, anchor_td_index + length_td + tol_td)

    # Lookup date labels for display (derived from indices)
    start_row = df_daily[df_daily['td_index'] == start_td].iloc[0]
    end_row = df_daily[df_daily['td_index'] == end_td].iloc[0]
    anchor_row = df_daily[df_daily['td_index'] == anchor_td_index].iloc[0]

    return {
        'start_td_index': int(start_td),
        'end_td_index': int(end_td),
        'anchor_td_index': int(anchor_td_index),
        'length_td': int(length_td),
        'tolerance_td': int(tol_td),
        'start_date_label': start_row['trading_date'] if 'trading_date' in start_row else str(start_row['timestamp'].date()),
        'end_date_label': end_row['trading_date'] if 'trading_date' in end_row else str(end_row['timestamp'].date()),
        'anchor_date_label': anchor_row['trading_date'] if 'trading_date' in anchor_row else str(anchor_row['timestamp'].date())
    }


def resolve_weekly_cycle_window(
    df_weekly: pd.DataFrame,
    anchor_tw_index: int,
    length_tw: int,
    tol_tw: int = 2
) -> Dict[str, Any]:
    """
    Resolve a weekly cycle window using trading-week indices only.

    NO calendar arithmetic. Only bar-index ranges.

    Args:
        df_weekly: Weekly dataframe with tw_index column
        anchor_tw_index: Anchor point (trading week index)
        length_tw: Cycle length in trading weeks
        tol_tw: Tolerance window in trading weeks (default 2TW)

    Returns:
        Dict with:
        - start_tw_index: int
        - end_tw_index: int
        - anchor_tw_index: int
        - length_tw: int
        - start_week_label: str (YYYY-MM-DD) for display only
        - end_week_label: str (YYYY-MM-DD) for display only
        - anchor_week_label: str (YYYY-MM-DD) for display only
    """
    if 'tw_index' not in df_weekly.columns:
        raise ValueError("DataFrame must have tw_index column")

    max_tw = df_weekly['tw_index'].max()

    # Validate anchor
    if anchor_tw_index < 0 or anchor_tw_index > max_tw:
        raise ValueError(f"anchor_tw_index {anchor_tw_index} out of range [0, {max_tw}]")

    # Calculate window bounds (pure bar-index arithmetic)
    start_tw = max(0, anchor_tw_index - length_tw - tol_tw)
    end_tw = min(max_tw, anchor_tw_index + length_tw + tol_tw)

    # Lookup date labels for display (derived from indices)
    start_row = df_weekly[df_weekly['tw_index'] == start_tw].iloc[0]
    end_row = df_weekly[df_weekly['tw_index'] == end_tw].iloc[0]
    anchor_row = df_weekly[df_weekly['tw_index'] == anchor_tw_index].iloc[0]

    return {
        'start_tw_index': int(start_tw),
        'end_tw_index': int(end_tw),
        'anchor_tw_index': int(anchor_tw_index),
        'length_tw': int(length_tw),
        'tolerance_tw': int(tol_tw),
        'start_week_label': start_row['week_end_date'] if 'week_end_date' in start_row else str(start_row['timestamp'].date()),
        'end_week_label': end_row['week_end_date'] if 'week_end_date' in end_row else str(end_row['timestamp'].date()),
        'anchor_week_label': anchor_row['week_end_date'] if 'week_end_date' in anchor_row else str(anchor_row['timestamp'].date())
    }
