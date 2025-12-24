"""Tests for charts module"""
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from riley.charts import generate_charts


def create_test_data():
    """Create test dataframe"""
    dates = pd.date_range(end='2025-01-01', periods=500, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(500) * 2)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 500),
        'symbol': 'TEST',
        'source': 'TEST',
        'timeframe': 'D'
    })
    return df


def create_test_pivots():
    """Create test pivots"""
    return [
        {
            'type': 'HIGH',
            'price': 105.0,
            'date': pd.Timestamp('2025-01-01'),
            'index': 400
        },
        {
            'type': 'LOW',
            'price': 95.0,
            'date': pd.Timestamp('2024-12-15'),
            'index': 380
        }
    ]


def test_charts_created():
    """Test that chart files are created"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "charts" / "TEST" / "2025-01-01"

        df = create_test_data()
        pivots = create_test_pivots()
        levels = {
            'poc_90d': 100.0,
            'poc_180d': 101.0,
            'poc_1y': 102.0,
            'range': {
                '20d': {'high': 110, 'low': 90, 'mid': 100},
                '60d': {'high': 115, 'low': 85, 'mid': 100}
            }
        }

        generate_charts(df, 'TEST', '2025-01-01', pivots, levels, output_dir)

        # Check files exist
        assert (output_dir / 'weekly.png').exists()
        assert (output_dir / 'daily.png').exists()

        # Check file size (should not be empty)
        weekly_size = (output_dir / 'weekly.png').stat().st_size
        daily_size = (output_dir / 'daily.png').stat().st_size

        assert weekly_size > 1000  # At least 1KB
        assert daily_size > 1000
