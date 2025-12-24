"""Chart generation v2 - trading bar index only, no calendar spacing"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
from typing import Dict, List, Any


def render_daily_weekly(
    df_daily: pd.DataFrame,
    df_weekly: pd.DataFrame,
    levels: Dict[str, Any],
    pivots: List[Dict[str, Any]],
    symbol: str,
    as_of_date: str,
    out_dir: Path
) -> None:
    """
    Generate daily and weekly charts using trading bar index (no calendar spacing).

    Args:
        df_daily: Sanitized daily data with td_index
        df_weekly: Sanitized weekly data with tw_index
        levels: Dict with POCs and ranges
        pivots: List of ranked pivots
        symbol: Instrument symbol
        as_of_date: As-of date string
        out_dir: Output directory
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Render daily chart
    daily_path = out_dir / "daily.png"
    _render_chart(
        df=df_daily,
        index_col='td_index',
        label_col='trading_date',
        window_size=252,
        levels=levels,
        pivots=pivots,
        symbol=symbol,
        timeframe='Daily',
        output_path=daily_path,
        min_pivot_spacing=10
    )
    print(f"charts_v2 wrote daily.png to {daily_path}")

    # Render weekly chart
    weekly_path = out_dir / "weekly.png"
    _render_chart(
        df=df_weekly,
        index_col='tw_index',
        label_col='week_end_label',
        window_size=260,
        levels=levels,
        pivots=pivots,
        symbol=symbol,
        timeframe='Weekly',
        output_path=weekly_path,
        min_pivot_spacing=4
    )
    print(f"charts_v2 wrote weekly.png to {weekly_path}")


def _render_chart(
    df: pd.DataFrame,
    index_col: str,
    label_col: str,
    window_size: int,
    levels: Dict[str, Any],
    pivots: List[Dict[str, Any]],
    symbol: str,
    timeframe: str,
    output_path: Path,
    min_pivot_spacing: int
) -> None:
    """
    Render a single chart (daily or weekly).

    Args:
        df: Data with integer index column
        index_col: Name of integer index column (td_index or tw_index)
        label_col: Name of date label column for tick labels
        window_size: Number of bars to show
        levels: Levels to plot
        pivots: Pivots to label
        symbol: Symbol name
        timeframe: 'Daily' or 'Weekly'
        output_path: Output file path
        min_pivot_spacing: Minimum spacing between pivot labels
    """
    # Extract window
    df_window = df.tail(window_size).copy()

    if df_window.empty:
        # Create empty chart
        fig, ax1 = plt.subplots(figsize=(16, 10))
        ax1.text(0.5, 0.5, 'No data', ha='center', va='center')
        fig.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return

    # Extract x (integer index) and OHLCV
    x = df_window[index_col].values
    opens = df_window['open'].values
    highs = df_window['high'].values
    lows = df_window['low'].values
    closes = df_window['close'].values
    volumes = df_window['volume'].values

    # Compute y-axis bounds from visible window only
    close_q01 = np.quantile(closes, 0.01)
    close_q99 = np.quantile(closes, 0.99)
    y_range = close_q99 - close_q01
    y_min = close_q01 - 0.02 * y_range
    y_max = close_q99 + 0.02 * y_range

    # Create figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10),
                                     gridspec_kw={'height_ratios': [4, 1]},
                                     sharex=True)

    # Plot candlesticks
    candle_width = 0.8
    for i in range(len(x)):
        x_pos = x[i]
        o, h, l, c = opens[i], highs[i], lows[i], closes[i]

        # Color
        color = 'green' if c >= o else 'red'

        # Wick (high-low line)
        ax1.plot([x_pos, x_pos], [l, h], color='black', linewidth=1, alpha=1.0)

        # Body (rectangle)
        body_height = abs(c - o)
        body_bottom = min(o, c)
        rect = Rectangle((x_pos - candle_width/2, body_bottom),
                         candle_width, body_height,
                         facecolor=color, edgecolor='black', linewidth=0.5, alpha=1.0)
        ax1.add_patch(rect)

    # Plot volume bars
    ax2.bar(x, volumes, width=candle_width, color='gray', alpha=0.5)

    # Plot levels
    if levels:
        # POCs
        if 'poc_90td' in levels and levels['poc_90td']:
            ax1.axhline(levels['poc_90td'], color='blue', linestyle='--',
                       linewidth=1, alpha=0.7, label='POC 90TD')
        if 'poc_180td' in levels and levels['poc_180td']:
            ax1.axhline(levels['poc_180td'], color='cyan', linestyle='--',
                       linewidth=1, alpha=0.7, label='POC 180TD')
        if 'poc_252td' in levels and levels['poc_252td']:
            ax1.axhline(levels['poc_252td'], color='purple', linestyle='--',
                       linewidth=1, alpha=0.7, label='POC 252TD')

        # Ranges
        if 'range' in levels:
            r = levels['range']
            if '20td_high' in r:
                ax1.axhline(r['20td_high'], color='orange', linestyle=':',
                           linewidth=1, alpha=0.5, label='20TD High')
            if '20td_low' in r:
                ax1.axhline(r['20td_low'], color='orange', linestyle=':',
                           linewidth=1, alpha=0.5, label='20TD Low')

    # Filter and plot pivots
    filtered_pivots = _filter_pivots_for_chart(pivots, df_window, index_col, min_pivot_spacing)

    for pivot in filtered_pivots:
        pivot_idx = pivot['index']
        pivot_price = pivot['price']
        pivot_type = pivot['type']

        # Only plot if in visible window
        if pivot_idx in x:
            color = 'darkgreen' if pivot_type == 'HIGH' else 'darkred'
            marker = 'v' if pivot_type == 'HIGH' else '^'
            ax1.plot(pivot_idx, pivot_price, marker=marker, color=color,
                    markersize=10, alpha=0.8)
            ax1.text(pivot_idx, pivot_price, f' {pivot_price:.2f}',
                    fontsize=8, color=color, ha='left', va='center')

    # Set y-axis limits
    ax1.set_ylim(y_min, y_max)

    # X-axis ticks (sparse date labels)
    tick_spacing = max(1, len(x) // 12)  # ~12 labels
    tick_positions = x[::tick_spacing]
    tick_labels = df_window[label_col].iloc[::tick_spacing].values

    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)

    # Labels
    ax1.set_title(f'{symbol} - {timeframe} ({len(df)} bars total, showing last {len(df_window)})')
    ax1.set_ylabel('Price')
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)

    ax2.set_ylabel('Volume')
    ax2.set_xlabel('Trading Date')
    ax2.grid(True, alpha=0.3)

    # Save
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)


def _filter_pivots_for_chart(
    pivots: List[Dict[str, Any]],
    df_window: pd.DataFrame,
    index_col: str,
    min_spacing: int
) -> List[Dict[str, Any]]:
    """
    Filter pivots for chart display - top 3 highs and top 3 lows with minimum spacing.

    Args:
        pivots: List of pivot dicts with 'index', 'price', 'type', 'score'
        df_window: Visible window DataFrame
        index_col: Name of index column
        min_spacing: Minimum spacing between labels (in bars)

    Returns:
        Filtered list of pivots to display
    """
    if not pivots:
        return []

    # Filter to window
    window_indices = set(df_window[index_col].values)
    window_pivots = [p for p in pivots if p['index'] in window_indices]

    # Separate highs and lows
    highs = [p for p in window_pivots if p['type'] == 'HIGH']
    lows = [p for p in window_pivots if p['type'] == 'LOW']

    # Sort by score descending (higher score = more important = show first)
    highs.sort(key=lambda p: p.get('score', 0), reverse=True)
    lows.sort(key=lambda p: p.get('score', 0), reverse=True)

    # Select top 3 with spacing
    selected_highs = _select_with_spacing(highs, min_spacing)[:3]
    selected_lows = _select_with_spacing(lows, min_spacing)[:3]

    return selected_highs + selected_lows


def _select_with_spacing(pivots: List[Dict[str, Any]], min_spacing: int) -> List[Dict[str, Any]]:
    """
    Select pivots with minimum spacing between them.

    Args:
        pivots: List of pivots sorted by rank
        min_spacing: Minimum spacing in bars

    Returns:
        Filtered list
    """
    if not pivots:
        return []

    selected = [pivots[0]]

    for pivot in pivots[1:]:
        # Check spacing against all already selected
        if all(abs(pivot['index'] - s['index']) >= min_spacing for s in selected):
            selected.append(pivot)

    return selected
