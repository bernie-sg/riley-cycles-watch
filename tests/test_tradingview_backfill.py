"""Tests for TradingView backfill logic"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from riley.merge import merge_tradingview_with_ibkr, aggregate_to_weekly


def create_test_bars(start_date, periods, symbol='TEST', source='TEST'):
    """Helper to create test bar data"""
    dates = pd.date_range(start=start_date, periods=periods, freq='D', tz='UTC')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(periods) * 2)

    return pd.DataFrame({
        'timestamp': dates,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, periods),
        'symbol': symbol,
        'source': source,
        'timeframe': 'D'
    })


def test_merge_no_overlap():
    """Test merging datasets with no overlap"""
    tv_df = create_test_bars('2020-01-01', 100, source='TRADINGVIEW')
    ibkr_df = create_test_bars('2020-05-01', 50, source='IBKR')

    merged = merge_tradingview_with_ibkr(tv_df, ibkr_df)

    # Should have all bars from both
    assert len(merged) == 150
    assert merged['timestamp'].is_monotonic_increasing
    assert not merged['timestamp'].duplicated().any()


def test_merge_with_overlap():
    """Test merging datasets with overlapping timestamps"""
    tv_df = create_test_bars('2020-01-01', 100, source='TRADINGVIEW')
    ibkr_df = create_test_bars('2020-03-01', 50, source='IBKR')

    # Calculate expected overlap
    tv_end = tv_df['timestamp'].max()
    ibkr_start = ibkr_df['timestamp'].min()
    overlap_expected = (tv_end - ibkr_start).days + 1

    merged = merge_tradingview_with_ibkr(tv_df, ibkr_df)

    # Should deduplicate overlapping timestamps
    expected_rows = len(tv_df) + len(ibkr_df) - overlap_expected
    assert len(merged) == expected_rows
    assert not merged['timestamp'].duplicated().any()


def test_merge_ibkr_preference():
    """Test that IBKR data is preferred in overlaps"""
    # Create overlapping data with different volumes
    tv_df = create_test_bars('2020-01-01', 10, source='TRADINGVIEW')
    tv_df['volume'] = 1000  # Low volume

    ibkr_df = create_test_bars('2020-01-01', 10, source='IBKR')
    ibkr_df['volume'] = 5000  # High volume

    merged = merge_tradingview_with_ibkr(tv_df, ibkr_df)

    # Should have 10 bars (fully overlapping)
    assert len(merged) == 10

    # Should prefer IBKR volume
    assert (merged['volume'] == 5000).all()


def test_merge_volume_fallback():
    """Test volume fallback when IBKR volume is 0"""
    tv_df = create_test_bars('2020-01-01', 10, source='TRADINGVIEW')
    tv_df['volume'] = 1000

    ibkr_df = create_test_bars('2020-01-01', 10, source='IBKR')
    ibkr_df['volume'] = 0  # IBKR has no volume

    merged = merge_tradingview_with_ibkr(tv_df, ibkr_df)

    # Should use TradingView volume when IBKR is 0
    assert len(merged) == 10
    assert (merged['volume'] == 1000).all()


def test_merge_empty_tv():
    """Test merging when TradingView is empty"""
    tv_df = pd.DataFrame()
    ibkr_df = create_test_bars('2020-01-01', 50, source='IBKR')

    merged = merge_tradingview_with_ibkr(tv_df, ibkr_df)

    assert len(merged) == 50
    assert merged.equals(ibkr_df)


def test_merge_empty_ibkr():
    """Test merging when IBKR is empty"""
    tv_df = create_test_bars('2020-01-01', 50, source='TRADINGVIEW')
    ibkr_df = pd.DataFrame()

    merged = merge_tradingview_with_ibkr(tv_df, ibkr_df)

    assert len(merged) == 50
    assert merged.equals(tv_df)


def test_dedupe_removes_duplicates():
    """Test that deduplication works"""
    tv_df = create_test_bars('2020-01-01', 100, source='TRADINGVIEW')
    ibkr_df = tv_df.copy()
    ibkr_df['source'] = 'IBKR'

    merged = merge_tradingview_with_ibkr(tv_df, ibkr_df)

    # Should remove all duplicates
    assert len(merged) == 100
    assert not merged['timestamp'].duplicated().any()


def test_aggregate_to_weekly():
    """Test daily to weekly aggregation"""
    # Create 4 weeks of daily data
    daily_df = create_test_bars('2020-01-01', 28, source='TEST')

    # Set specific values for first week to test aggregation
    daily_df.loc[0:6, 'open'] = [100, 101, 102, 103, 104, 105, 106]
    daily_df.loc[0:6, 'high'] = [110, 111, 112, 113, 114, 115, 116]
    daily_df.loc[0:6, 'low'] = [90, 91, 92, 93, 94, 95, 96]
    daily_df.loc[0:6, 'close'] = [105, 106, 107, 108, 109, 110, 111]
    daily_df.loc[0:6, 'volume'] = [1000, 2000, 3000, 4000, 5000, 6000, 7000]

    weekly_df = aggregate_to_weekly(daily_df)

    # Should have ~4 weeks
    assert len(weekly_df) >= 3
    assert len(weekly_df) <= 5

    # Check aggregation logic for first week
    first_week = weekly_df.iloc[0]

    # Open should be first day's open
    assert first_week['open'] == 100

    # High should be max
    assert first_week['high'] == 116

    # Low should be min
    assert first_week['low'] == 90

    # Close should be last day's close
    assert first_week['close'] == 111

    # Volume should be sum
    assert first_week['volume'] == 28000


def test_aggregate_preserves_metadata():
    """Test that weekly aggregation preserves symbol and updates source"""
    daily_df = create_test_bars('2020-01-01', 28, symbol='ES', source='MERGED')

    weekly_df = aggregate_to_weekly(daily_df)

    assert (weekly_df['symbol'] == 'ES').all()
    assert (weekly_df['timeframe'] == 'W').all()
    assert (weekly_df['source'] == 'MERGED').all()


def test_load_tradingview_different_formats():
    """Test loading TradingView CSVs with different column formats"""
    from riley.data import load_tradingview_history_folder

    with tempfile.TemporaryDirectory() as tmpdir:
        folder = Path(tmpdir)

        # Format 1: lowercase
        csv1 = folder / "format1.csv"
        csv1.write_text("time,open,high,low,close,volume\n"
                       "1609459200,100,102,98,101,1000\n"
                       "1609545600,101,103,99,102,2000\n")

        # Format 2: capitalized
        csv2 = folder / "format2.csv"
        csv2.write_text("Time,Open,High,Low,Close,Volume\n"
                       "1609632000,102,104,100,103,3000\n"
                       "1609718400,103,105,101,104,4000\n")

        df = load_tradingview_history_folder(str(folder), symbol='TEST')

        assert len(df) == 4
        assert 'timestamp' in df.columns
        assert 'open' in df.columns
        assert 'volume' in df.columns
        assert not df['timestamp'].duplicated().any()
