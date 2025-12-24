"""Test weekly_v2 ISO week grouping"""
import sys
from pathlib import Path
import pandas as pd

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.weekly_v2 import make_weekly_from_daily


def test_weekly_grouping_by_iso_week():
    """Test that daily bars are grouped by ISO week correctly"""
    # Create daily data spanning 3 weeks with some missing days
    dates = [
        '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05',  # Week 1
        '2024-01-08', '2024-01-09', '2024-01-10', '2024-01-11', '2024-01-12',  # Week 2
        '2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19',  # Week 3
    ]

    df_daily = pd.DataFrame({
        'td_index': range(len(dates)),
        'trading_date': dates,
        'open': 100.0 + pd.Series(range(len(dates))),
        'high': 101.0 + pd.Series(range(len(dates))),
        'low': 99.0 + pd.Series(range(len(dates))),
        'close': 100.5 + pd.Series(range(len(dates))),
        'volume': 1000000
    })

    df_weekly = make_weekly_from_daily(df_daily)

    # Should have 3 weeks
    assert len(df_weekly) == 3, f"Expected 3 weeks, got {len(df_weekly)}"

    # Check tw_index starts at 0
    assert df_weekly['tw_index'].iloc[0] == 0
    assert df_weekly['tw_index'].iloc[-1] == 2

    # Check OHLC aggregation
    # First week: open from first bar, close from last bar
    assert df_weekly['open'].iloc[0] == 100.0
    assert df_weekly['close'].iloc[0] == 100.5 + 3  # 4th bar (index 3)

    print("✓ Weekly grouping by ISO week works correctly")


def test_weekly_filters_out_short_weeks():
    """Test that weeks with < 3 trading days are dropped"""
    # Create data with one short week (2 days) and one full week (5 days)
    dates = [
        '2024-01-02', '2024-01-03',  # Week 1: 2 days (should be dropped)
        '2024-01-08', '2024-01-09', '2024-01-10', '2024-01-11', '2024-01-12',  # Week 2: 5 days
    ]

    df_daily = pd.DataFrame({
        'td_index': range(len(dates)),
        'trading_date': dates,
        'open': 100.0,
        'high': 101.0,
        'low': 99.0,
        'close': 100.5,
        'volume': 1000000
    })

    df_weekly = make_weekly_from_daily(df_daily)

    # Should have only 1 week (the short one dropped)
    assert len(df_weekly) == 1, f"Expected 1 week, got {len(df_weekly)}"

    print("✓ Weeks with < 3 trading days are filtered out")


def test_weekly_filters_out_zero_volume():
    """Test that weeks with zero volume are dropped"""
    dates = [
        '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05',
    ]

    df_daily = pd.DataFrame({
        'td_index': range(len(dates)),
        'trading_date': dates,
        'open': 100.0,
        'high': 101.0,
        'low': 99.0,
        'close': 100.5,
        'volume': [0, 0, 0, 0]  # All zero volume
    })

    df_weekly = make_weekly_from_daily(df_daily)

    # Should have 0 weeks (zero volume dropped)
    assert len(df_weekly) == 0, f"Expected 0 weeks, got {len(df_weekly)}"

    print("✓ Weeks with zero volume are filtered out")


if __name__ == '__main__':
    test_weekly_grouping_by_iso_week()
    test_weekly_filters_out_short_weeks()
    test_weekly_filters_out_zero_volume()
    print("\n✓ All weekly grouping tests passed")
