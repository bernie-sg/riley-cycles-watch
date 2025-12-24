"""Tests for IBKR module"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock


def test_stub_mode_data_loading():
    """Test loading data in stub mode (no IBKR connection required)"""
    from riley.data import load_or_stub_data

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Load with use_ibkr=False (stub mode)
        df = load_or_stub_data('ES', project_root, use_ibkr=False)

        assert len(df) > 0
        assert 'timestamp' in df.columns
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns


def test_append_only_no_duplicates():
    """Test that append logic prevents duplicate timestamps"""
    from riley.data import load_or_stub_data

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # First load (stub mode)
        df1 = load_or_stub_data('ES', project_root, use_ibkr=False)
        initial_count = len(df1)

        # Second load (should return same data, no fetch)
        df2 = load_or_stub_data('ES', project_root, use_ibkr=False)

        assert len(df2) == initial_count
        assert df2['timestamp'].duplicated().sum() == 0


@patch('riley.ibkr.IB')
def test_ibkr_connection_mock(mock_ib_class):
    """Test IBKR connection with mock"""
    from riley.ibkr import connect_ibkr

    # Create mock IB instance
    mock_ib = MagicMock()
    mock_ib_class.return_value = mock_ib

    # Test connection
    ib = connect_ibkr()

    # Verify connection was attempted
    mock_ib.connect.assert_called_once()
    assert ib == mock_ib


@patch('riley.ibkr.IB')
def test_fetch_historical_bars_schema(mock_ib_class):
    """Test that fetched bars have correct schema"""
    from riley.ibkr import fetch_ibkr_historical_bars

    # Create mock bars
    mock_bars = []
    dates = pd.date_range(end='2025-01-01', periods=100, freq='D', tz='UTC')
    for i, date in enumerate(dates):
        bar = Mock()
        bar.date = date
        bar.open = 100 + i * 0.1
        bar.high = 101 + i * 0.1
        bar.low = 99 + i * 0.1
        bar.close = 100.5 + i * 0.1
        bar.volume = 1000000 + i * 1000
        mock_bars.append(bar)

    # Mock IB instance
    mock_ib = MagicMock()
    mock_ib.reqHistoricalData.return_value = mock_bars
    mock_ib_class.return_value = mock_ib

    # Fetch data
    df = fetch_ibkr_historical_bars(
        symbol='ES',
        timeframe='D',
        start_date=None,
        end_date=datetime(2025, 1, 1, tzinfo=timezone.utc)
    )

    # Verify schema
    required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"

    # Verify data types
    assert pd.api.types.is_datetime64_any_dtype(df['timestamp'])
    assert len(df) == 100


@patch('riley.ibkr.IB')
def test_weekly_aggregation(mock_ib_class):
    """Test that daily bars are correctly aggregated to weekly"""
    from riley.ibkr import fetch_ibkr_historical_bars

    # Create mock daily bars spanning multiple weeks
    mock_bars = []
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D', tz='UTC')
    for i, date in enumerate(dates):
        bar = Mock()
        bar.date = date
        bar.open = 100 + np.sin(i / 10) * 10
        bar.high = 102 + np.sin(i / 10) * 10
        bar.low = 98 + np.sin(i / 10) * 10
        bar.close = 101 + np.sin(i / 10) * 10
        bar.volume = 1000000 + i * 1000
        mock_bars.append(bar)

    mock_ib = MagicMock()
    mock_ib.reqHistoricalData.return_value = mock_bars
    mock_ib_class.return_value = mock_ib

    # Fetch weekly data
    df = fetch_ibkr_historical_bars(
        symbol='ES',
        timeframe='W',
        start_date=None,
        end_date=datetime(2024, 12, 31, tzinfo=timezone.utc)
    )

    # Weekly bars should be fewer than daily bars
    assert len(df) < len(mock_bars)
    assert len(df) > 0

    # Verify weekly bars have valid OHLCV
    assert (df['high'] >= df['low']).all()
    assert (df['high'] >= df['open']).all()
    assert (df['high'] >= df['close']).all()
    assert (df['low'] <= df['open']).all()
    assert (df['low'] <= df['close']).all()


def test_unsupported_symbol_raises_error():
    """Test that unsupported symbols raise ValueError"""
    from riley.ibkr import fetch_ibkr_historical_bars

    with pytest.raises(ValueError, match="Unsupported symbol"):
        fetch_ibkr_historical_bars(
            symbol='INVALID',
            timeframe='D',
            start_date=None,
            end_date=datetime(2025, 1, 1, tzinfo=timezone.utc)
        )


def test_invalid_timeframe_raises_error():
    """Test that invalid timeframe raises ValueError"""
    from riley.ibkr import fetch_ibkr_historical_bars

    with pytest.raises(ValueError, match="Invalid timeframe"):
        fetch_ibkr_historical_bars(
            symbol='ES',
            timeframe='X',
            start_date=None,
            end_date=datetime(2025, 1, 1, tzinfo=timezone.utc)
        )


@patch('riley.ibkr.IB')
def test_connection_retry_logic(mock_ib_class):
    """Test that connection retries once on failure"""
    from riley.ibkr import connect_ibkr

    mock_ib = MagicMock()
    mock_ib.connect.side_effect = [Exception("First attempt failed"), None]
    mock_ib_class.return_value = mock_ib

    # Should succeed on retry
    ib = connect_ibkr()

    # Verify connect was called twice
    assert mock_ib.connect.call_count == 2


@patch('riley.ibkr.IB')
def test_connection_fails_after_retry(mock_ib_class):
    """Test that connection raises error after retry fails"""
    from riley.ibkr import connect_ibkr

    mock_ib = MagicMock()
    mock_ib.connect.side_effect = Exception("Connection failed")
    mock_ib_class.return_value = mock_ib

    with pytest.raises(ConnectionError, match="Failed to connect"):
        connect_ibkr()


@patch('riley.ibkr.IB')
def test_no_data_raises_error(mock_ib_class):
    """Test that empty result from IBKR raises RuntimeError"""
    from riley.ibkr import fetch_ibkr_historical_bars

    mock_ib = MagicMock()
    mock_ib.reqHistoricalData.return_value = []  # Empty result
    mock_ib_class.return_value = mock_ib

    with pytest.raises(RuntimeError, match="IBKR returned no data"):
        fetch_ibkr_historical_bars(
            symbol='ES',
            timeframe='D',
            start_date=None,
            end_date=datetime(2025, 1, 1, tzinfo=timezone.utc)
        )


@patch('riley.ibkr.fetch_ibkr_historical_bars')
def test_append_only_behavior(mock_fetch):
    """Test that only new bars are fetched when data exists"""
    from riley.data import load_or_stub_data

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Create initial data
        initial_dates = pd.date_range(end='2024-12-01', periods=100, freq='D', tz='UTC')
        initial_df = pd.DataFrame({
            'timestamp': initial_dates,
            'open': 100.0,
            'high': 101.0,
            'low': 99.0,
            'close': 100.5,
            'volume': 1000000,
            'symbol': 'ES',
            'source': 'IBKR',
            'timeframe': 'D'
        })

        # Save initial data
        processed_path = project_root / "data" / "processed" / "ES" / "D.parquet"
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        initial_df.to_parquet(processed_path)

        # Mock new bars
        new_dates = pd.date_range(start='2024-12-02', end='2024-12-10', freq='D', tz='UTC')
        new_df = pd.DataFrame({
            'timestamp': new_dates,
            'open': 101.0,
            'high': 102.0,
            'low': 100.0,
            'close': 101.5,
            'volume': 1100000
        })
        mock_fetch.return_value = new_df

        # Load data (should fetch only new bars)
        result_df = load_or_stub_data('ES', project_root, use_ibkr=True)

        # Verify append behavior
        assert len(result_df) > len(initial_df)
        assert result_df['timestamp'].min() == initial_dates[0]
        assert result_df['timestamp'].duplicated().sum() == 0
