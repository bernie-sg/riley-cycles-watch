#!/usr/bin/env python3
"""
Timebase Enforcement Tests for Riley Project

These tests ensure TRADING-BAR TIMEBASE is strictly enforced:
- NO calendar arithmetic (timedelta for windows)
- NO pd.date_range for defining windows
- All lookback windows use bar counts (.tail(N))
- All data has td_index and/or tw_index
"""
import pytest
import sys
from pathlib import Path
import pandas as pd
import re

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.features import (
    detect_pivots, compute_volume_profile, compute_range_context,
    compute_volatility_regime, compute_trend_regime
)
from riley.cycles import resolve_daily_cycle_window, resolve_weekly_cycle_window


def test_no_forbidden_patterns_in_source():
    """
    Scan source files for forbidden calendar arithmetic patterns.
    """
    forbidden_patterns = [
        (r'pd\.Timedelta\(days=\d+\)', 'pd.Timedelta(days=N) for window calculation'),
        (r'timedelta\(days=\d+\)', 'timedelta(days=N) for window calculation'),
        (r'pd\.date_range', 'pd.date_range for window definition'),
        (r'\.dt\.days', 'Converting timedelta to days for window calculation')
    ]

    src_dir = project_root / "src" / "riley"
    violations = []

    for py_file in src_dir.glob("*.py"):
        if py_file.name in ["__init__.py", "database.py", "reports.py", "data.py"]:
            continue  # Skip non-computation files (data.py uses calendar arithmetic for ingestion/stub generation)

        content = py_file.read_text()

        for pattern, description in forbidden_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                # Check if it's in a comment (basic heuristic)
                line_start = content.rfind('\n', 0, match.start()) + 1
                line = content[line_start:content.find('\n', match.start())]
                if not line.strip().startswith('#'):
                    violations.append(f"{py_file.name}:{description} - '{match.group()}'")

    assert len(violations) == 0, f"Calendar arithmetic detected:\n" + "\n".join(violations)


def test_volume_profile_uses_trading_bars():
    """Volume profile must use trading-bar lookback windows."""
    df = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=300, freq='D'),
        'high': [100 + i * 0.1 for i in range(300)],
        'low': [99 + i * 0.1 for i in range(300)],
        'close': [99.5 + i * 0.1 for i in range(300)],
        'volume': [1000000] * 300
    })

    result = compute_volume_profile(df)

    # Should have td-suffixed keys
    assert 'poc_90td' in result
    assert 'poc_180td' in result
    assert 'poc_252td' in result

    # Should NOT have day-suffixed keys
    assert 'poc_90d' not in result
    assert 'poc_180d' not in result
    assert 'poc_1y' not in result


def test_range_context_uses_trading_bars():
    """Range context must use trading-bar lookback windows."""
    df = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=300, freq='D'),
        'high': [100 + i * 0.1 for i in range(300)],
        'low': [99 + i * 0.1 for i in range(300)],
        'close': [99.5 + i * 0.1 for i in range(300)]
    })

    result = compute_range_context(df)

    # Should have td-suffixed keys
    assert '20td' in result
    assert '60td' in result
    assert '252td' in result

    # Should NOT have day-suffixed keys
    assert '20d' not in result
    assert '60d' not in result
    assert '1y' not in result


def test_daily_cycle_window_pure_bar_index():
    """Daily cycle resolution must use pure bar-index arithmetic."""
    df = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=100, freq='D'),
        'td_index': range(100),
        'close': [100] * 100
    })

    # Resolve a 20TD cycle anchored at TD50
    result = resolve_daily_cycle_window(df, anchor_td_index=50, length_td=20, tol_td=5)

    # Check result structure
    assert 'start_td_index' in result
    assert 'end_td_index' in result
    assert 'anchor_td_index' in result
    assert 'length_td' in result
    assert 'tolerance_td' in result

    # Verify pure bar-index arithmetic
    assert result['start_td_index'] == 50 - 20 - 5  # 25
    assert result['end_td_index'] == min(99, 50 + 20 + 5)  # 75
    assert result['anchor_td_index'] == 50
    assert result['length_td'] == 20
    assert result['tolerance_td'] == 5

    # Date labels should exist but are for display only
    assert 'start_date_label' in result
    assert 'end_date_label' in result
    assert 'anchor_date_label' in result


def test_weekly_cycle_window_pure_bar_index():
    """Weekly cycle resolution must use pure bar-index arithmetic."""
    df = pd.DataFrame({
        'timestamp': pd.date_range('2023-01-01', periods=52, freq='W'),
        'tw_index': range(52),
        'close': [100] * 52
    })

    # Resolve a 10TW cycle anchored at TW30
    result = resolve_weekly_cycle_window(df, anchor_tw_index=30, length_tw=10, tol_tw=2)

    # Check result structure
    assert 'start_tw_index' in result
    assert 'end_tw_index' in result
    assert 'anchor_tw_index' in result
    assert 'length_tw' in result
    assert 'tolerance_tw' in result

    # Verify pure bar-index arithmetic
    assert result['start_tw_index'] == 30 - 10 - 2  # 18
    assert result['end_tw_index'] == min(51, 30 + 10 + 2)  # 42
    assert result['anchor_tw_index'] == 30
    assert result['length_tw'] == 10
    assert result['tolerance_tw'] == 2


def test_daily_data_must_have_td_index():
    """All daily processed data must have td_index column."""
    daily_parquet = project_root / "data" / "ES" / "daily.parquet"

    if daily_parquet.exists():
        df = pd.read_parquet(daily_parquet)
        assert 'td_index' in df.columns, "daily.parquet missing td_index column"
        assert df['td_index'].is_monotonic_increasing, "td_index must be monotonically increasing"
        assert df['td_index'].iloc[0] == 0, "td_index must start at 0"


def test_weekly_data_must_have_tw_index():
    """All weekly processed data must have tw_index column."""
    weekly_parquet = project_root / "data" / "ES" / "weekly.parquet"

    if weekly_parquet.exists():
        df = pd.read_parquet(weekly_parquet)
        assert 'tw_index' in df.columns, "weekly.parquet missing tw_index column"
        assert df['tw_index'].is_monotonic_increasing, "tw_index must be monotonically increasing"
        assert df['tw_index'].iloc[0] == 0, "tw_index must start at 0"


def test_no_timedelta_in_lookback_windows():
    """Ensure lookback windows use .tail(N), not timedelta-based filtering."""
    # Read source files and check for date-based filtering patterns
    src_dir = project_root / "src" / "riley"

    forbidden_lookback_patterns = [
        r'df\[df\[.timestamp.\]\s*>=.*days',  # df[df['timestamp'] >= X days ago]
        r'\.loc\[.*timestamp.*-.*days',        # .loc[timestamp - N days]
    ]

    violations = []

    for py_file in src_dir.glob("*.py"):
        if py_file.name in ["__init__.py", "database.py", "reports.py", "data.py"]:
            continue  # Skip non-computation files

        content = py_file.read_text()

        for pattern in forbidden_lookback_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                violations.append(f"{py_file.name}: {match.group()}")

    assert len(violations) == 0, f"Timedelta-based lookback detected:\n" + "\n".join(violations)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
