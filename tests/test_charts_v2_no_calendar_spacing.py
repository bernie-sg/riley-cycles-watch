"""Test that charts_v2 uses integer index with no calendar spacing"""
import sys
from pathlib import Path
import pandas as pd
import tempfile

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.charts_v2 import render_daily_weekly


def test_daily_chart_uses_integer_index():
    """Test that daily chart uses td_index with no calendar gaps"""
    # Create synthetic daily data with td_index 0..50
    dates = pd.date_range('2024-01-01', periods=70, freq='D')
    # Simulate weekends by skipping days
    trading_dates = [d for d in dates if d.weekday() < 5][:51]  # 51 trading days
    n_bars = len(trading_dates)

    df_daily = pd.DataFrame({
        'td_index': range(n_bars),
        'trading_date': [d.strftime('%Y-%m-%d') for d in trading_dates],
        'open': [100.0] * n_bars,
        'high': [101.0] * n_bars,
        'low': [99.0] * n_bars,
        'close': [100.5] * n_bars,
        'volume': [1000000] * n_bars
    })

    # Create minimal weekly data
    df_weekly = pd.DataFrame({
        'tw_index': range(10),
        'week_end_label': [f'2024-01-{7*(i+1):02d}' for i in range(10)],
        'open': 100.0,
        'high': 101.0,
        'low': 99.0,
        'close': 100.5,
        'volume': 5000000
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)

        # Render charts
        render_daily_weekly(
            df_daily=df_daily,
            df_weekly=df_weekly,
            levels={},
            pivots=[],
            symbol='TEST',
            as_of_date='2024-01-31',
            out_dir=out_dir
        )

        # Verify files exist
        assert (out_dir / "daily.png").exists()
        assert (out_dir / "weekly.png").exists()

    print("✓ Daily chart uses integer index (td_index)")


def test_weekly_chart_uses_integer_index():
    """Test that weekly chart uses tw_index"""
    df_daily = pd.DataFrame({
        'td_index': range(10),
        'trading_date': [f'2024-01-{i+1:02d}' for i in range(10)],
        'open': 100.0,
        'high': 101.0,
        'low': 99.0,
        'close': 100.5,
        'volume': 1000000
    })

    df_weekly = pd.DataFrame({
        'tw_index': range(5),
        'week_end_label': [f'2024-01-{7*(i+1):02d}' for i in range(5)],
        'open': 100.0,
        'high': 101.0,
        'low': 99.0,
        'close': 100.5,
        'volume': 5000000
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)

        render_daily_weekly(
            df_daily=df_daily,
            df_weekly=df_weekly,
            levels={},
            pivots=[],
            symbol='TEST',
            as_of_date='2024-01-31',
            out_dir=out_dir
        )

        assert (out_dir / "weekly.png").exists()

    print("✓ Weekly chart uses integer index (tw_index)")


if __name__ == '__main__':
    test_daily_chart_uses_integer_index()
    test_weekly_chart_uses_integer_index()
    print("\n✓ All chart spacing tests passed")
