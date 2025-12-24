"""Tests for data module"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
from riley.data import load_or_stub_data


def test_data_append_no_duplicates():
    """Test that data append logic prevents duplicates"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # First load - creates stub data
        df1 = load_or_stub_data('TEST', project_root, use_ibkr=False)
        assert len(df1) > 0
        assert 'timestamp' in df1.columns
        assert 'close' in df1.columns

        # Second load - should return same data (no duplicates)
        df2 = load_or_stub_data('TEST', project_root, use_ibkr=False)
        assert len(df2) == len(df1)

        # Verify timestamps are unique
        assert df2['timestamp'].duplicated().sum() == 0


def test_stub_data_schema():
    """Test that stub data conforms to standard schema"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        df = load_or_stub_data('TEST', project_root, use_ibkr=False)

        required_columns = ['timestamp', 'open', 'high', 'low', 'close',
                           'volume', 'symbol', 'source', 'timeframe']

        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"

        assert df['symbol'].iloc[0] == 'TEST'
        assert df['source'].iloc[0] == 'STUB'
        assert df['timeframe'].iloc[0] == 'D'
