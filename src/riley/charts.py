"""Chart generation for Riley Project"""
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any


def generate_charts(df: pd.DataFrame, symbol: str, as_of_date: str,
                    pivots: List[Dict[str, Any]], levels: Dict[str, Any],
                    output_dir: Path):
    """
    Generate weekly and daily charts with labels.

    Charts include:
    - Price candles
    - Volume bars
    - Labeled pivots
    - Horizontal level lines
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Weekly chart (5Y or max available)
    weekly_data = df.tail(252 * 5)  # ~5 years
    weekly_path = output_dir / "weekly.png"
    _create_chart(weekly_data, symbol, as_of_date, pivots, levels, weekly_path, "Weekly")

    # Daily chart (1Y)
    daily_data = df.tail(252)  # ~1 year
    daily_path = output_dir / "daily.png"
    _create_chart(daily_data, symbol, as_of_date, pivots, levels, daily_path, "Daily")


def _filter_pivots_for_chart(pivots: List[Dict[str, Any]], df: pd.DataFrame,
                              chart_type: str) -> List[Dict[str, Any]]:
    """
    Filter pivots for chart visualization to prevent label spam.

    Rules:
    - Show top 3 ranked pivots per side (HIGH/LOW)
    - Or show pivots separated by ≥ 2 ATR from last labeled pivot
    - Weekly charts: major pivots only (top 2 per side)
    """
    if not pivots:
        return []

    # Compute ATR for spacing
    df_copy = df.copy()
    df_copy['tr'] = np.maximum(
        df_copy['high'] - df_copy['low'],
        np.maximum(
            abs(df_copy['high'] - df_copy['close'].shift(1)),
            abs(df_copy['low'] - df_copy['close'].shift(1))
        )
    )
    atr = df_copy['tr'].rolling(14).mean().iloc[-1]

    # Separate by type
    highs = [p for p in pivots if p['type'] == 'HIGH']
    lows = [p for p in pivots if p['type'] == 'LOW']

    # Limit by chart type
    max_per_side = 2 if chart_type == "Weekly" else 3

    # Filter by rank and spacing
    def filter_by_spacing(pivot_list, max_count):
        selected = []
        for pivot in pivot_list[:max_count * 2]:  # Check top 2x max for spacing
            if len(selected) >= max_count:
                break
            # Check spacing from all selected
            if not selected:
                selected.append(pivot)
            else:
                min_distance = min(abs(pivot['price'] - s['price']) for s in selected)
                if min_distance >= 2 * atr:
                    selected.append(pivot)
        return selected[:max_count]

    filtered_highs = filter_by_spacing(highs, max_per_side)
    filtered_lows = filter_by_spacing(lows, max_per_side)

    return filtered_highs + filtered_lows


def _create_chart(df: pd.DataFrame, symbol: str, as_of_date: str,
                  pivots: List[Dict[str, Any]], levels: Dict[str, Any],
                  output_path: Path, chart_type: str):
    """Create a single chart with all labels and price scale protection"""

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), height_ratios=[3, 1],
                                     sharex=True, gridspec_kw={'hspace': 0.05})

    # Price scale protection
    price_quantile_01 = df['low'].quantile(0.01)
    price_quantile_99 = df['high'].quantile(0.99)
    median_price_252 = df['close'].rolling(min(252, len(df)), min_periods=1).median().iloc[-1]

    # Never allow chart min < 0.8 × median(252TD)
    y_min = max(price_quantile_01, 0.8 * median_price_252)
    y_max = price_quantile_99

    # Plot candlesticks with full opacity
    for idx in range(len(df)):
        row = df.iloc[idx]
        date = row['timestamp']
        open_price = row['open']
        high = row['high']
        low = row['low']
        close = row['close']

        color = 'green' if close >= open_price else 'red'
        alpha = 1.0  # Full opacity to fix ghosting

        # High-low line
        ax1.plot([date, date], [low, high], color=color, linewidth=0.5, alpha=alpha)

        # Body
        body_height = abs(close - open_price)
        body_bottom = min(open_price, close)
        rect = Rectangle((mdates.date2num(date) - 0.3, body_bottom),
                         0.6, body_height, facecolor=color, edgecolor=color, alpha=alpha)
        ax1.add_patch(rect)

    # Filter pivots for chart
    filtered_pivots = _filter_pivots_for_chart(pivots, df, chart_type)

    # Plot filtered pivots
    for pivot in filtered_pivots:
        if pivot['date'] >= df['timestamp'].min():
            marker = 'v' if pivot['type'] == 'HIGH' else '^'
            color = 'red' if pivot['type'] == 'HIGH' else 'green'
            y_pos = pivot['price']

            ax1.plot(pivot['date'], y_pos, marker=marker, markersize=8,
                    color=color, markerfacecolor=color, markeredgecolor='black', markeredgewidth=0.5)

            # Label with non-overlapping offset
            date_str = pivot['date'].strftime('%Y-%m-%d')
            label = f"{pivot['type']}\n{pivot['price']:.2f}\n{date_str}"
            offset = 1.01 if pivot['type'] == 'HIGH' else 0.99
            ax1.text(pivot['date'], y_pos * offset, label, fontsize=7,
                    ha='center', va='top' if pivot['type'] == 'HIGH' else 'bottom')

    # Plot horizontal levels (trading-bar based)
    if 'poc_90td' in levels and levels['poc_90td']:
        ax1.axhline(levels['poc_90td'], color='blue', linestyle='--', linewidth=1, alpha=0.5, label='90TD POC')
    if 'poc_180td' in levels and levels['poc_180td']:
        ax1.axhline(levels['poc_180td'], color='purple', linestyle='--', linewidth=1, alpha=0.5, label='180TD POC')
    if 'poc_252td' in levels and levels['poc_252td']:
        ax1.axhline(levels['poc_252td'], color='orange', linestyle='--', linewidth=1, alpha=0.5, label='252TD POC')

    # Plot range levels
    if 'range' in levels:
        for window, color in [('20td', 'cyan'), ('60td', 'magenta')]:
            if window in levels['range']:
                r = levels['range'][window]
                ax1.axhline(r['high'], color=color, linestyle=':', linewidth=0.8, alpha=0.3)
                ax1.axhline(r['low'], color=color, linestyle=':', linewidth=0.8, alpha=0.3)

    # Apply price scale protection
    ax1.set_ylim(y_min, y_max)

    ax1.set_ylabel('Price')
    ax1.set_title(f"{symbol} - {chart_type} - as of {as_of_date}")
    ax1.legend(loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3)

    # Volume bars with full opacity
    colors = ['green' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'red'
              for i in range(len(df))]
    ax2.bar(df['timestamp'], df['volume'], color=colors, alpha=1.0, width=0.8)
    ax2.set_ylabel('Volume')
    ax2.set_xlabel('Date')
    ax2.grid(True, alpha=0.3)

    # Format x-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"Chart saved: {output_path}")
