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
    benchmark_price: float = None
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

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Add quadrant backgrounds
    _add_quadrant_backgrounds(fig)

    # Add crosshair at (100, 100)
    _add_crosshair(fig)

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
        end_date_str = end_date.strftime('%B %d, %Y')
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
            range=[88, 112],
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        ),
        yaxis=dict(
            title=dict(
                text='JdK RS-Momentum',
                font=dict(size=CHART_CONFIG['axis_font_size'])
            ),
            range=[95, 105],
            showgrid=True,
            gridcolor='lightgray',
            zeroline=False
        ),
        plot_bgcolor='white',
        width=CHART_CONFIG['width'],
        height=CHART_CONFIG['height'],
        hovermode='closest',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )

    return fig


def _add_quadrant_backgrounds(fig: go.Figure):
    """Add colored quadrant backgrounds to the chart."""
    for quadrant_name, quadrant in QUADRANTS.items():
        x_min, x_max = quadrant['x_range']
        y_min, y_max = quadrant['y_range']

        # Clip to reasonable display range
        x_min = max(x_min, 88)
        x_max = min(x_max, 112)
        y_min = max(y_min, 95)
        y_max = min(y_max, 105)

        # Add rectangle
        fig.add_shape(
            type='rect',
            x0=x_min, y0=y_min,
            x1=x_max, y1=y_max,
            fillcolor=quadrant['color'],
            line=dict(width=0),
            layer='below'
        )

        # Add quadrant label
        x_pos = x_min + (x_max - x_min) * 0.05
        y_pos = y_max - (y_max - y_min) * 0.05

        fig.add_annotation(
            x=x_pos,
            y=y_pos,
            text=quadrant['name'],
            showarrow=False,
            font=dict(size=14, color='gray'),
            xanchor='left',
            yanchor='top'
        )


def _add_crosshair(fig: go.Figure):
    """Add crosshair lines at (100, 100)."""
    # Vertical line at x=100
    fig.add_shape(
        type='line',
        x0=100, y0=95,
        x1=100, y1=105,
        line=dict(
            color=CHART_CONFIG['crosshair_color'],
            width=CHART_CONFIG['crosshair_width']
        ),
        layer='above'
    )

    # Horizontal line at y=100
    fig.add_shape(
        type='line',
        x0=88, y0=100,
        x1=112, y1=100,
        line=dict(
            color=CHART_CONFIG['crosshair_color'],
            width=CHART_CONFIG['crosshair_width']
        ),
        layer='above'
    )


def auto_scale_axes(df: pd.DataFrame, symbols: List[str], end_date: pd.Timestamp, padding: float = 0.1) -> Dict:
    """
    Auto-calculate axis ranges based on data.

    Args:
        df: DataFrame with rs_ratio and rs_momentum
        symbols: List of symbols to include
        end_date: Latest date
        padding: Padding factor (default 10%)

    Returns:
        Dict with x_range and y_range
    """
    latest_data = df[(df['symbol'].isin(symbols)) & (df['date'] == end_date)]

    if latest_data.empty:
        return {'x_range': [88, 112], 'y_range': [95, 105]}

    x_vals = latest_data['rs_ratio'].values
    y_vals = latest_data['rs_momentum'].values

    x_min, x_max = x_vals.min(), x_vals.max()
    y_min, y_max = y_vals.min(), y_vals.max()

    x_range_size = x_max - x_min
    y_range_size = y_max - y_min

    # Add padding
    x_min -= x_range_size * padding
    x_max += x_range_size * padding
    y_min -= y_range_size * padding
    y_max += y_range_size * padding

    # Ensure 100 is always visible
    x_min = min(x_min, 99)
    x_max = max(x_max, 101)
    y_min = min(y_min, 99)
    y_max = max(y_max, 101)

    return {
        'x_range': [x_min, x_max],
        'y_range': [y_min, y_max]
    }
