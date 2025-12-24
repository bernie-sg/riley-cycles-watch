"""Tests for UI database queries"""
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import CyclesDB


@pytest.fixture
def temp_db():
    """Create a temporary test database"""
    fd, path = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)

    # Create minimal schema
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE instruments (
            instrument_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'CANONICAL',
            canonical_symbol TEXT,
            active INTEGER DEFAULT 1,
            instrument_type TEXT DEFAULT 'FUTURES',
            sector TEXT DEFAULT 'UNCLASSIFIED',
            group_name TEXT DEFAULT 'FUTURES',
            sort_key INTEGER DEFAULT 1000
        )
    """)

    cursor.execute("""
        CREATE TABLE daily_scan_runs (
            scan_run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_td_label TEXT NOT NULL UNIQUE,
            scan_tw_label TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE daily_scan_rows (
            scan_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_run_id INTEGER NOT NULL,
            instrument_id INTEGER NOT NULL,
            daily_status TEXT,
            weekly_status TEXT,
            days_to_daily_core_start INTEGER,
            weeks_to_weekly_core_start INTEGER,
            overlap_flag INTEGER DEFAULT 0,
            priority_score REAL DEFAULT 0.0,
            daily_core_start_label TEXT,
            daily_core_end_label TEXT,
            daily_median_label TEXT,
            weekly_core_start_label TEXT,
            weekly_core_end_label TEXT,
            weekly_median_label TEXT,
            daily_prewindow_start_label TEXT,
            daily_prewindow_end_label TEXT,
            weekly_prewindow_start_label TEXT,
            weekly_prewindow_end_label TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE desk_notes (
            note_id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_id INTEGER NOT NULL,
            asof_td_label TEXT NOT NULL,
            author TEXT,
            note_type TEXT,
            bullets_json TEXT,
            source TEXT,
            timeframe_scope TEXT,
            price_reference TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE astro_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_id INTEGER NOT NULL,
            event_input_date_label TEXT NOT NULL,
            snapped_td_label TEXT,
            snapped_td_index INTEGER,
            role TEXT,
            name TEXT,
            category TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE cycle_specs (
            cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_id INTEGER NOT NULL,
            timeframe TEXT NOT NULL,
            version INTEGER NOT NULL,
            anchor_input_date_label TEXT,
            cycle_length_bars INTEGER
        )
    """)

    # Insert test data
    cursor.execute("""
        INSERT INTO instruments (symbol, name, group_name, sector, sort_key)
        VALUES ('ES', 'E-mini S&P 500', 'FUTURES', 'INDICES', 100)
    """)

    cursor.execute("""
        INSERT INTO daily_scan_runs (scan_td_label, scan_tw_label, created_at)
        VALUES ('2025-12-22', '2025-12-20', '2025-12-22 10:00:00')
    """)

    cursor.execute("""
        INSERT INTO daily_scan_rows (
            scan_run_id, instrument_id, daily_status, weekly_status,
            days_to_daily_core_start, overlap_flag, priority_score
        )
        VALUES (1, 1, 'IN_WINDOW', 'APPROACHING', 0, 0, 100.0)
    """)

    conn.commit()
    conn.close()

    yield path

    # Cleanup
    os.unlink(path)


def test_get_latest_scan_date(temp_db):
    """Test getting latest scan date"""
    db = CyclesDB(temp_db)
    latest = db.get_latest_scan_date()
    assert latest == '2025-12-22'


def test_get_today_rows(temp_db):
    """Test getting today rows"""
    db = CyclesDB(temp_db)
    df = db.get_today_rows('2025-12-22')
    assert not df.empty
    assert 'symbol' in df.columns
    assert 'daily_status' in df.columns
    assert df.iloc[0]['symbol'] == 'ES'


def test_update_instrument_taxonomy(temp_db):
    """Test updating instrument taxonomy"""
    db = CyclesDB(temp_db)

    # Update
    success = db.update_instrument_taxonomy('ES', {
        'group_name': 'INDICES',
        'sector': 'EQUITY_INDICES',
        'sort_key': 50
    })
    assert success

    # Verify
    df = db.get_instruments()
    es_row = df[df['symbol'] == 'ES'].iloc[0]
    assert es_row['group_name'] == 'INDICES'
    assert es_row['sector'] == 'EQUITY_INDICES'
    assert es_row['sort_key'] == 50


def test_get_instruments(temp_db):
    """Test getting instruments list"""
    db = CyclesDB(temp_db)
    df = db.get_instruments()
    assert not df.empty
    assert 'symbol' in df.columns
    assert 'group_name' in df.columns
    assert df.iloc[0]['symbol'] == 'ES'


def test_get_group_names(temp_db):
    """Test getting distinct group names"""
    db = CyclesDB(temp_db)
    groups = db.get_group_names()
    assert 'FUTURES' in groups


def test_get_sectors(temp_db):
    """Test getting distinct sectors"""
    db = CyclesDB(temp_db)
    sectors = db.get_sectors()
    assert 'INDICES' in sectors


def test_get_countdown_rows(temp_db):
    """Test getting countdown rows"""
    db = CyclesDB(temp_db)
    df = db.get_countdown_rows('2025-12-22', horizon_td=15, horizon_tw=6)
    # May be empty if no upcoming events in test data
    assert isinstance(df, type(None)) or 'symbol' in df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
