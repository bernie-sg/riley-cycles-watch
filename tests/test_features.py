"""Tests for features module"""
import pytest
import pandas as pd
import numpy as np
from riley.features import (
    detect_pivots, rank_pivots, compute_volume_profile,
    compute_range_context, compute_volatility_regime, compute_trend_regime
)


def create_test_data(n=100):
    """Create sample dataframe for testing"""
    dates = pd.date_range(end='2025-01-01', periods=n, freq='D')
    np.random.seed(42)

    # Create price series with clear swings
    prices = 100 + np.cumsum(np.random.randn(n) * 2)

    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, n),
        'symbol': 'TEST',
        'source': 'TEST',
        'timeframe': 'D'
    })
    return df


def test_pivot_detection_consistent():
    """Test that pivot detection returns consistent results"""
    df = create_test_data(100)

    # Run pivot detection twice
    pivots1 = detect_pivots(df, left=2, right=2)
    pivots2 = detect_pivots(df, left=2, right=2)

    # Should be deterministic
    assert len(pivots1) == len(pivots2)

    for p1, p2 in zip(pivots1, pivots2):
        assert p1['type'] == p2['type']
        assert p1['price'] == p2['price']
        assert p1['index'] == p2['index']


def test_pivot_structure():
    """Test that pivots have required fields"""
    df = create_test_data(100)
    pivots = detect_pivots(df, left=2, right=2)

    assert len(pivots) > 0, "Should detect some pivots"

    for pivot in pivots:
        assert 'type' in pivot
        assert pivot['type'] in ['HIGH', 'LOW']
        assert 'price' in pivot
        assert 'date' in pivot
        assert 'index' in pivot
        assert isinstance(pivot['price'], (float, np.floating))


def test_rank_pivots():
    """Test pivot ranking logic"""
    df = create_test_data(100)
    pivots = detect_pivots(df, left=2, right=2)

    if len(pivots) > 0:
        ranked = rank_pivots(pivots, df, top_n=5)

        assert len(ranked) <= 5
        assert len(ranked) <= len(pivots)

        # Check score exists
        for pivot in ranked:
            assert 'score' in pivot


def test_volume_profile():
    """Test volume profile computation"""
    df = create_test_data(300)
    vol_profile = compute_volume_profile(df)

    assert 'poc_90d' in vol_profile
    assert 'poc_180d' in vol_profile
    assert 'poc_1y' in vol_profile

    # POCs should be reasonable prices
    if vol_profile['poc_90d']:
        assert vol_profile['poc_90d'] > 0


def test_range_context():
    """Test range context computation"""
    df = create_test_data(300)
    range_context = compute_range_context(df)

    assert '20d' in range_context
    assert '60d' in range_context
    assert '252d' in range_context
    assert 'current' in range_context

    # Check structure
    assert 'high' in range_context['20d']
    assert 'low' in range_context['20d']
    assert 'mid' in range_context['20d']

    # High should be >= Low
    assert range_context['20d']['high'] >= range_context['20d']['low']


def test_volatility_regime():
    """Test volatility regime computation"""
    df = create_test_data(300)
    vol_regime = compute_volatility_regime(df)

    assert 'atr' in vol_regime
    assert 'percentile' in vol_regime
    assert 'regime' in vol_regime
    assert vol_regime['regime'] in ['LOW', 'NORMAL', 'HIGH']


def test_trend_regime():
    """Test trend regime computation"""
    df = create_test_data(300)
    trend_regime = compute_trend_regime(df)

    assert 'current' in trend_regime
    assert 'ma50' in trend_regime
    assert 'ma200' in trend_regime
    assert 'regime' in trend_regime
    assert trend_regime['regime'] in ['UPTREND', 'DOWNTREND', 'CHOPPY']
