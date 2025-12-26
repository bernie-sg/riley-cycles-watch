"""
Constants and configuration for RRG Sector Rotation Map
"""

# US Sector ETFs (SPDR Select Sector Funds)
US_SECTORS = {
    'XLK': 'Technology',
    'XLY': 'Consumer Discretionary',
    'XLC': 'Communication Services',
    'XLV': 'Health Care',
    'XLF': 'Financials',
    'XLE': 'Energy',
    'XLI': 'Industrials',
    'XLP': 'Consumer Staples',
    'XLU': 'Utilities',
    'XLB': 'Materials',
    'XLRE': 'Real Estate'
}

# Quadrant definitions
QUADRANTS = {
    'improving': {
        'name': 'Improving',
        'x_range': (0, 100),
        'y_range': (100, float('inf')),
        'color': 'rgba(173, 216, 230, 0.3)'  # Light blue
    },
    'leading': {
        'name': 'Leading',
        'x_range': (100, float('inf')),
        'y_range': (100, float('inf')),
        'color': 'rgba(144, 238, 144, 0.3)'  # Light green
    },
    'weakening': {
        'name': 'Weakening',
        'x_range': (100, float('inf')),
        'y_range': (0, 100),
        'color': 'rgba(255, 255, 153, 0.3)'  # Light yellow
    },
    'lagging': {
        'name': 'Lagging',
        'x_range': (0, 100),
        'y_range': (0, 100),
        'color': 'rgba(255, 182, 193, 0.3)'  # Light pink/red
    }
}

# Default RRG parameters
DEFAULT_PARAMS = {
    'rs_smoothing': 10,           # EMA period for RS smoothing
    'ratio_lookback': 10,         # Rolling mean period for RS-Ratio calculation
    'momentum_lookback': 10,      # Rolling mean period for RS-Momentum calculation
    'tail_weeks': 5,              # Number of weeks to show in tail
    'benchmark': 'SPY'            # Default benchmark
}

# Chart styling
CHART_CONFIG = {
    'width': 1200,
    'height': 700,
    'title_font_size': 24,
    'axis_font_size': 12,
    'label_font_size': 10,
    'crosshair_color': 'black',
    'crosshair_width': 2,
    'tail_width': 2,
    'tail_opacity': 0.6,
    'point_size': 10,
    'latest_point_size': 14
}

# Color palette for sector tails
SECTOR_COLORS = {
    'XLK': '#1f77b4',  # Blue
    'XLY': '#ff7f0e',  # Orange
    'XLC': '#2ca02c',  # Green
    'XLV': '#d62728',  # Red
    'XLF': '#9467bd',  # Purple
    'XLE': '#8c564b',  # Brown
    'XLI': '#e377c2',  # Pink
    'XLP': '#7f7f7f',  # Gray
    'XLU': '#bcbd22',  # Yellow-green
    'XLB': '#17becf',  # Cyan
    'XLRE': '#ff9896'  # Light red
}
