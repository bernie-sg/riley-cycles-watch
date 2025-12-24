"""Tests for packets module"""
import pytest
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import json
from riley.packets import write_packets


def create_test_data():
    """Create test dataframe"""
    dates = pd.date_range(end='2025-01-01', periods=100, freq='D')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 2)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, 100),
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
            'index': 50
        },
        {
            'type': 'LOW',
            'price': 95.0,
            'date': pd.Timestamp('2024-12-15'),
            'index': 40
        }
    ]


def test_packet_files_created():
    """Test that all packet files are created"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "TEST" / "2025-01-01"

        df = create_test_data()
        pivots = create_test_pivots()
        vol_profile = {'poc_90d': 100.0, 'poc_180d': 101.0, 'poc_1y': 102.0}
        range_context = {
            '20d': {'high': 110, 'low': 90, 'mid': 100},
            '60d': {'high': 115, 'low': 85, 'mid': 100},
            '252d': {'high': 120, 'low': 80, 'mid': 100},
            'current': 100
        }
        volatility_regime = {'atr': 2.5, 'percentile': 50.0, 'regime': 'NORMAL'}
        trend_regime = {'current': 100, 'ma50': 98, 'ma200': 95, 'regime': 'UPTREND'}

        packet_path = write_packets(
            'TEST', '2025-01-01', df, pivots, vol_profile,
            range_context, volatility_regime, trend_regime, output_dir
        )

        # Check all files exist
        assert (output_dir / 'context.json').exists()
        assert (output_dir / 'levels.json').exists()
        assert (output_dir / 'pivots.json').exists()
        assert (output_dir / 'volume.json').exists()
        assert (output_dir / 'gamma.json').exists()
        assert (output_dir / 'diff.json').exists()
        assert (output_dir / 'packet.json').exists()
        assert packet_path == output_dir / 'packet.json'


def test_packet_json_structure():
    """Test that packet.json has correct structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "TEST" / "2025-01-01"

        df = create_test_data()
        pivots = create_test_pivots()
        vol_profile = {'poc_90d': 100.0, 'poc_180d': 101.0, 'poc_1y': 102.0}
        range_context = {
            '20d': {'high': 110, 'low': 90, 'mid': 100},
            '60d': {'high': 115, 'low': 85, 'mid': 100},
            '252d': {'high': 120, 'low': 80, 'mid': 100},
            'current': 100
        }
        volatility_regime = {'atr': 2.5, 'percentile': 50.0, 'regime': 'NORMAL'}
        trend_regime = {'current': 100, 'ma50': 98, 'ma200': 95, 'regime': 'UPTREND'}

        write_packets(
            'TEST', '2025-01-01', df, pivots, vol_profile,
            range_context, volatility_regime, trend_regime, output_dir
        )

        # Load and verify packet.json
        with open(output_dir / 'packet.json', 'r') as f:
            packet = json.load(f)

        assert packet['symbol'] == 'TEST'
        assert packet['as_of_date'] == '2025-01-01'
        assert 'files' in packet
        assert 'cycles' in packet
        assert packet['cycles']['status'] == 'missing'


def test_levels_json_structure():
    """Test that levels.json has correct structure"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "TEST" / "2025-01-01"

        df = create_test_data()
        pivots = create_test_pivots()
        vol_profile = {'poc_90d': 100.0, 'poc_180d': 101.0, 'poc_1y': 102.0}
        range_context = {
            '20d': {'high': 110, 'low': 90, 'mid': 100},
            '60d': {'high': 115, 'low': 85, 'mid': 100},
            '252d': {'high': 120, 'low': 80, 'mid': 100},
            'current': 100
        }
        volatility_regime = {'atr': 2.5, 'percentile': 50.0, 'regime': 'NORMAL'}
        trend_regime = {'current': 100, 'ma50': 98, 'ma200': 95, 'regime': 'UPTREND'}

        write_packets(
            'TEST', '2025-01-01', df, pivots, vol_profile,
            range_context, volatility_regime, trend_regime, output_dir
        )

        # Load and verify levels.json
        with open(output_dir / 'levels.json', 'r') as f:
            levels = json.load(f)

        assert 'levels' in levels
        assert len(levels['levels']) > 0

        # Check level structure
        for level in levels['levels']:
            assert 'tier' in level
            assert 'level_price' in level
            assert 'source' in level
            assert 'label' in level
