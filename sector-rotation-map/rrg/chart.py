"""
Plotly chart builder for RRG visualization
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List
from .constants import QUADRANTS, CHART_CONFIG, SECTOR_COLORS, US_SECTORS
from .compute import get_tail_coordinates, get_latest_point


def create_rrg_chart(
    df: pd.DataFrame,
    symbols: List[str],
    end_date: pd.Timestamp,
    tail_weeks: int = 5,
    show_tails: bool = True,
    show_labels: bool = True,
    benchmark_symbol: str = 'SPY',
    benchmark_price: float = None,
    zoom_level: str = 'Normal'
) -> go.Figure:
    """
    Create the RRG scatter plot with quadrants and tails.

    Args:
        df: DataFrame with rs_ratio and rs_momentum
        symbols: List of symbols to plot
        end_date: Latest date for plotting
        tail_weeks: Number of weeks for tails
        show_tails: Whether to show historical tails
        show_labels: Whether to show symbol labels
        benchmark_symbol: Benchmark ticker
        benchmark_price: Current benchmark price for title
        zoom_level: Default zoom level ('Tight', 'Normal', 'Wide', 'Auto')

    Returns:
        Plotly Figure object
    """
    # Auto-scale axes based on actual data
    axis_ranges = auto_scale_axes(df, symbols, end_date, padding=0.15, zoom_level=zoom_level)

    fig = go.Figure()

    # Add quadrant backgrounds
    _add_quadrant_backgrounds(fig, axis_ranges)

    # Plot each sector
    for symbol in symbols:
        color = SECTOR_COLORS.get(symbol, '#000000')

        # Get tail coordinates
        if show_tails:
            tail = get_tail_coordinates(df, symbol, end_date, tail_weeks)
            if tail['x']:
                # Add tail line
                fig.add_trace(go.Scatter(
                    x=tail['x'],
                    y=tail['y'],
                    mode='lines+markers',
                    name=symbol,
                    line=dict(color=color, width=CHART_CONFIG['tail_width']),
                    marker=dict(size=6, opacity=CHART_CONFIG['tail_opacity']),
                    opacity=CHART_CONFIG['tail_opacity'],
                    hovertemplate=f'{symbol}<br>RS-Ratio: %{{x:.2f}}<br>RS-Momentum: %{{y:.2f}}<extra></extra>',
                    showlegend=False
                ))

        # Get latest point
        latest = get_latest_point(df, symbol, end_date)
        if latest['x'] is not None and latest['y'] is not None:
            # Add latest point (larger marker)
            fig.add_trace(go.Scatter(
                x=[latest['x']],
                y=[latest['y']],
                mode='markers+text' if show_labels else 'markers',
                name=symbol,
                marker=dict(
                    size=CHART_CONFIG['latest_point_size'],
                    color=color,
                    line=dict(width=2, color='white')
                ),
                text=[symbol] if show_labels else None,
                textposition='top center',
                textfont=dict(size=CHART_CONFIG['label_font_size'], color=color),
                hovertemplate=f'{symbol}<br>RS-Ratio: {latest["x"]:.2f}<br>RS-Momentum: {latest["y"]:.2f}<extra></extra>',
                showlegend=True
            ))

    # Update layout
    title_text = "Leadership is Rotating"
    if benchmark_price:
        end_date_str = end_date.strftime('%d %B %Y')
        title_text = f"${benchmark_price:.2f}  {benchmark_symbol} ({tail_weeks} weeks ending {end_date_str})<br><b>Leadership is Rotating</b>"

    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=CHART_CONFIG['title_font_size']),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=dict(
                text='JdK RS-Ratio',
                font=dict(size=CHART_CONFIG['axis_font_size'])
            ),
            range=axis_ranges['x_range'],
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        ),
        yaxis=dict(
            title=dict(
                text='JdK RS-Momentum',
                font=dict(size=CHART_CONFIG['axis_font_size'])
            ),
            range=axis_ranges['y_range'],
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        ),
        plot_bgcolor='white',
        width=CHART_CONFIG['width'],
        height=CHART_CONFIG['height'],
        hovermode='closest',
        dragmode='pan',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )

    return fig


def _add_quadrant_backgrounds(fig: go.Figure, axis_ranges: Dict):
    """Add colored quadrant backgrounds to the chart."""
    # Define fixed label positions using paper coordinates (0-1 range)
    # These will stay at the corners regardless of zoom level
    label_positions = {
        'improving': {
            'x': 0.02,  # 2% from left edge
            'y': 0.98,  # 2% from top edge
            'xref': 'paper',
            'yref': 'paper',
            'xanchor': 'left',
            'yanchor': 'top'
        },
        'leading': {
            'x': 0.98,  # 2% from right edge
            'y': 0.98,  # 2% from top edge
            'xref': 'paper',
            'yref': 'paper',
            'xanchor': 'right',
            'yanchor': 'top'
        },
        'weakening': {
            'x': 0.98,  # 2% from right edge
            'y': 0.02,  # 2% from bottom edge
            'xref': 'paper',
            'yref': 'paper',
            'xanchor': 'right',
            'yanchor': 'bottom'
        },
        'lagging': {
            'x': 0.02,  # 2% from left edge
            'y': 0.02,  # 2% from bottom edge
            'xref': 'paper',
            'yref': 'paper',
            'xanchor': 'left',
            'yanchor': 'bottom'
        }
    }

    for quadrant_name, quadrant in QUADRANTS.items():
        x_min, x_max = quadrant['x_range']
        y_min, y_max = quadrant['y_range']

        # Use very wide ranges for quadrants to extend beyond any reasonable zoom level
        # This ensures colored backgrounds are always visible
        if x_min == 0:
            x_min = 0
        if y_min == 0:
            y_min = 0
        if x_max == float('inf'):
            x_max = 200  # Extend far beyond typical data range
        if y_max == float('inf'):
            y_max = 200  # Extend far beyond typical data range

        # Add rectangle
        fig.add_shape(
            type='rect',
            x0=x_min, y0=y_min,
            x1=x_max, y1=y_max,
            fillcolor=quadrant['color'],
            line=dict(width=0),
            layer='below'
        )

        # Add quadrant label at fixed corner position using paper coordinates
        label_pos = label_positions[quadrant_name]
        fig.add_annotation(
            x=label_pos['x'],
            y=label_pos['y'],
            xref=label_pos['xref'],
            yref=label_pos['yref'],
            text=f"<b>{quadrant['name']}</b>",
            showarrow=False,
            font=dict(size=18, color='dimgray'),
            xanchor=label_pos['xanchor'],
            yanchor=label_pos['yanchor'],
            bgcolor='rgba(255, 255, 255, 0.7)',
            borderpad=4
        )


def _add_crosshair(fig: go.Figure, axis_ranges: Dict):
    """Add crosshair lines at (100, 100)."""
    # Vertical line at x=100
    fig.add_shape(
        type='line',
        x0=100, y0=axis_ranges['y_range'][0],
        x1=100, y1=axis_ranges['y_range'][1],
        line=dict(
            color=CHART_CONFIG['crosshair_color'],
            width=CHART_CONFIG['crosshair_width']
        ),
        layer='above'
    )

    # Horizontal line at y=100
    fig.add_shape(
        type='line',
        x0=axis_ranges['x_range'][0], y0=100,
        x1=axis_ranges['x_range'][1], y1=100,
        line=dict(
            color=CHART_CONFIG['crosshair_color'],
            width=CHART_CONFIG['crosshair_width']
        ),
        layer='above'
    )


def auto_scale_axes(df: pd.DataFrame, symbols: List[str], end_date: pd.Timestamp, padding: float = 0.1, zoom_level: str = 'Normal') -> Dict:
    """
    Auto-calculate axis ranges based on data and zoom level.

    Args:
        df: DataFrame with rs_ratio and rs_momentum
        symbols: List of symbols to include
        end_date: Latest date
        padding: Padding factor (default 10%)
        zoom_level: Zoom level ('Tight', 'Normal', 'Wide', 'Auto')

    Returns:
        Dict with x_range and y_range
    """
    latest_data = df[(df['symbol'].isin(symbols)) & (df['date'] == end_date)]

    if latest_data.empty:
        return {'x_range': [95, 105], 'y_range': [97, 103]}

    x_vals = latest_data['rs_ratio'].values
    y_vals = latest_data['rs_momentum'].values

    x_min, x_max = x_vals.min(), x_vals.max()
    y_min, y_max = y_vals.min(), y_vals.max()

    # Define zoom level presets
    if zoom_level == 'Tight':
        # Tight zoom for closely clustered stocks
        default_x_min, default_x_max = 98, 102
        default_y_min, default_y_max = 98.5, 101.5
    elif zoom_level == 'Wide':
        # Wide zoom for commodities and wide spreads
        default_x_min, default_x_max = 90, 110
        default_y_min, default_y_max = 95, 105
    elif zoom_level == 'Auto':
        # Full auto-scale - fit all data with padding
        x_spread = x_max - x_min
        y_spread = y_max - y_min

        # Ensure minimum spread
        if x_spread < 2:
            x_spread = 2
        if y_spread < 2:
            y_spread = 2

        x_range_low = x_min - x_spread * padding
        x_range_high = x_max + x_spread * padding
        y_range_low = y_min - y_spread * padding
        y_range_high = y_max + y_spread * padding

        # Ensure 100,100 is always visible
        x_range_low = min(x_range_low, 99)
        x_range_high = max(x_range_high, 101)
        y_range_low = min(y_range_low, 99)
        y_range_high = max(y_range_high, 101)

        return {
            'x_range': [x_range_low, x_range_high],
            'y_range': [y_range_low, y_range_high]
        }
    else:  # Normal (default)
        # Normal zoom - good balance for stocks
        default_x_min, default_x_max = 95, 105
        default_y_min, default_y_max = 97, 103

    # For Tight, Normal, Wide: use preset defaults but expand if data is outside
    if x_min < default_x_min:
        x_range_low = x_min - (x_max - x_min) * padding
    else:
        x_range_low = default_x_min

    if x_max > default_x_max:
        x_range_high = x_max + (x_max - x_min) * padding
    else:
        x_range_high = default_x_max

    if y_min < default_y_min:
        y_range_low = y_min - (y_max - y_min) * padding
    else:
        y_range_low = default_y_min

    if y_max > default_y_max:
        y_range_high = y_max + (y_max - y_min) * padding
    else:
        y_range_high = default_y_max

    # Ensure 100,100 is always visible
    x_range_low = min(x_range_low, 99)
    x_range_high = max(x_range_high, 101)
    y_range_low = min(y_range_low, 99)
    y_range_high = max(y_range_high, 101)

    return {
        'x_range': [x_range_low, x_range_high],
        'y_range': [y_range_low, y_range_high]
    }
