"""Cycles Watch core logic - calendar snapping and projection math"""
import pandas as pd
from typing import List, Dict, Tuple, Any


def snap_to_next_trading_day(daily_calendar: pd.DataFrame, date_label: str) -> Tuple[int, str]:
    """
    Snap date label to next trading day in calendar.

    Args:
        daily_calendar: DataFrame with td_index, trading_date_label
        date_label: Input date string (YYYY-MM-DD)

    Returns:
        (td_index, trading_date_label) of next trading day >= date_label
    """
    # Find first trading day >= date_label
    matching = daily_calendar[daily_calendar['trading_date_label'] >= date_label]

    if matching.empty:
        raise ValueError(f"No trading day found on or after {date_label}")

    first_match = matching.iloc[0]
    return int(first_match['td_index']), str(first_match['trading_date_label'])


def td_to_label(daily_calendar: pd.DataFrame, td_index: int) -> str:
    """Get trading date label from td_index"""
    row = daily_calendar[daily_calendar['td_index'] == td_index]
    if row.empty:
        raise ValueError(f"td_index {td_index} not found in calendar")
    return str(row.iloc[0]['trading_date_label'])


def tw_to_label(weekly_calendar: pd.DataFrame, tw_index: int) -> str:
    """Get week end label from tw_index"""
    row = weekly_calendar[weekly_calendar['tw_index'] == tw_index]
    if row.empty:
        raise ValueError(f"tw_index {tw_index} not found in calendar")
    return str(row.iloc[0]['week_end_label'])


def compute_projections_daily(
    td_calendar: pd.DataFrame,
    anchor_label: str,
    cycle_length_td: int,
    minus_td: int,
    plus_td: int,
    prelead_td: int,
    k_min: int,
    k_max: int
) -> List[Dict[str, Any]]:
    """
    Compute daily cycle projections.

    Args:
        td_calendar: Daily calendar DataFrame
        anchor_label: Anchor date label
        cycle_length_td: Cycle length in trading days
        minus_td: Window minus (bars before median)
        plus_td: Window plus (bars after median)
        prelead_td: Prewindow lead (bars before core start)
        k_min: Minimum k value
        k_max: Maximum k value

    Returns:
        List of projection dicts
    """
    # Snap anchor to trading day
    anchor_index, anchor_label_snapped = snap_to_next_trading_day(td_calendar, anchor_label)

    projections = []

    for k in range(k_min, k_max + 1):
        median_index = anchor_index + k * cycle_length_td
        core_start = median_index - minus_td
        core_end = median_index + plus_td
        pre_start = core_start - prelead_td
        pre_end = core_start - 1

        # Get labels (handle out-of-range indices)
        try:
            median_label = td_to_label(td_calendar, median_index)
        except ValueError:
            median_label = f"td_{median_index}"

        projections.append({
            'k': k,
            'anchor_index': anchor_index,
            'anchor_label': anchor_label_snapped,
            'median_index': median_index,
            'median_label': median_label,
            'core_start_index': core_start,
            'core_end_index': core_end,
            'prewindow_start_index': pre_start,
            'prewindow_end_index': pre_end
        })

    return projections


def compute_projections_weekly(
    tw_calendar: pd.DataFrame,
    anchor_label: str,
    cycle_length_tw: int,
    minus_tw: int,
    plus_tw: int,
    prelead_tw: int,
    k_min: int,
    k_max: int
) -> List[Dict[str, Any]]:
    """
    Compute weekly cycle projections.

    Args:
        tw_calendar: Weekly calendar DataFrame
        anchor_label: Anchor week end label
        cycle_length_tw: Cycle length in trading weeks
        minus_tw: Window minus (weeks before median)
        plus_tw: Window plus (weeks after median)
        prelead_tw: Prewindow lead (weeks before core start)
        k_min: Minimum k value
        k_max: Maximum k value

    Returns:
        List of projection dicts
    """
    # Find closest week >= anchor_label
    matching = tw_calendar[tw_calendar['week_end_label'] >= anchor_label]
    if matching.empty:
        raise ValueError(f"No trading week found on or after {anchor_label}")

    anchor_index = int(matching.iloc[0]['tw_index'])
    anchor_label_snapped = str(matching.iloc[0]['week_end_label'])

    projections = []

    for k in range(k_min, k_max + 1):
        median_index = anchor_index + k * cycle_length_tw
        core_start = median_index - minus_tw
        core_end = median_index + plus_tw
        pre_start = core_start - prelead_tw
        pre_end = core_start - 1

        # Get labels
        try:
            median_label = tw_to_label(tw_calendar, median_index)
        except ValueError:
            median_label = f"tw_{median_index}"

        projections.append({
            'k': k,
            'anchor_index': anchor_index,
            'anchor_label': anchor_label_snapped,
            'median_index': median_index,
            'median_label': median_label,
            'core_start_index': core_start,
            'core_end_index': core_end,
            'prewindow_start_index': pre_start,
            'prewindow_end_index': pre_end
        })

    return projections
