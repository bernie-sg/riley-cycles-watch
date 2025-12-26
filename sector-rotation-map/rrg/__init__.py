"""
RRG (Relative Rotation Graph) package for sector rotation analysis.
"""

from .constants import US_SECTORS, DEFAULT_PARAMS
from .data import load_csv, detect_mode, filter_by_date, get_sector_universe, prepare_table_data
from .compute import compute_rrg_metrics, get_tail_coordinates, get_latest_point
from .chart import create_rrg_chart

__version__ = '1.0.0'

__all__ = [
    'US_SECTORS',
    'DEFAULT_PARAMS',
    'load_csv',
    'detect_mode',
    'filter_by_date',
    'get_sector_universe',
    'prepare_table_data',
    'compute_rrg_metrics',
    'get_tail_coordinates',
    'get_latest_point',
    'create_rrg_chart'
]
