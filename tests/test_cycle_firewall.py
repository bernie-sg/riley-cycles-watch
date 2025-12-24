"""
Tests for Cycle Write Firewall

Proves that corruption cannot recur with the new API.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.riley.cycle_service import CycleService
from src.riley.cycle_validation import validate_cycles, CycleValidationError


@pytest.fixture
def test_db():
    """Create a temporary test database with minimal schema"""
    fd, path = tempfile.mkstemp(suffix='.sqlite')
    os.close(fd)

    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # Create minimal schema
    cursor.execute("""
        CREATE TABLE instruments (
            instrument_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT,
            role TEXT DEFAULT 'CANONICAL',
            active INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE cycle_specs (
            cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            instrument_id INTEGER NOT NULL,
            timeframe TEXT NOT NULL,
            anchor_input_date_label TEXT NOT NULL,
            median_input_date_label TEXT,
            snap_rule TEXT NOT NULL DEFAULT 'NEXT_BAR',
            cycle_length_bars INTEGER NOT NULL,
            window_minus_bars INTEGER NOT NULL DEFAULT 3,
            window_plus_bars INTEGER NOT NULL DEFAULT 3,
            prewindow_lead_bars INTEGER NOT NULL DEFAULT 2,
            version INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            source TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE cycle_projections (
            projection_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_id INTEGER NOT NULL,
            instrument_id INTEGER NOT NULL,
            timeframe TEXT NOT NULL CHECK(timeframe IN ('DAILY','WEEKLY')),
            version INTEGER NOT NULL,
            anchor_index INTEGER NOT NULL,
            anchor_label TEXT NOT NULL,
            k INTEGER NOT NULL,
            median_index INTEGER NOT NULL,
            median_label TEXT NOT NULL,
            core_start_index INTEGER NOT NULL,
            core_end_index INTEGER NOT NULL,
            prewindow_start_index INTEGER NOT NULL,
            prewindow_end_index INTEGER NOT NULL,
            computed_at TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            notes TEXT,
            median_td_index INTEGER,
            core_start_td_index INTEGER,
            core_end_td_index INTEGER,
            prewindow_start_td_index INTEGER,
            prewindow_end_td_index INTEGER,
            median_tw_index INTEGER,
            core_start_tw_index INTEGER,
            core_end_tw_index INTEGER,
            prewindow_start_tw_index INTEGER,
            prewindow_end_tw_index INTEGER,
            core_start_label TEXT,
            core_end_label TEXT,
            prewindow_start_label TEXT,
            prewindow_end_label TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE trading_calendar_daily (
            td_index INTEGER PRIMARY KEY,
            trading_date_label TEXT NOT NULL UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE trading_calendar_weekly (
            instrument_id INTEGER NOT NULL DEFAULT 0,
            tw_index INTEGER NOT NULL,
            week_end_label TEXT NOT NULL,
            PRIMARY KEY (instrument_id, tw_index)
        )
    """)

    # Create unique index on projections
    cursor.execute("""
        CREATE UNIQUE INDEX uq_cycle_proj
        ON cycle_projections(instrument_id, timeframe, version, k)
    """)

    # Insert test instrument
    cursor.execute("""
        INSERT INTO instruments (symbol, name, role)
        VALUES ('TEST', 'Test Instrument', 'CANONICAL')
    """)

    # Insert daily calendar (simplified)
    for i in range(50):
        date_label = f"2025-12-{i+1:02d}"
        cursor.execute("""
            INSERT INTO trading_calendar_daily (td_index, trading_date_label)
            VALUES (?, ?)
        """, (i, date_label))

    # Insert weekly calendar (simplified)
    for i in range(20):
        week_label = f"2025-12-{i*7+1:02d}"
        cursor.execute("""
            INSERT INTO trading_calendar_weekly (instrument_id, tw_index, week_end_label)
            VALUES (0, ?, ?)
        """, (i, week_label))

    conn.commit()
    conn.close()

    yield path

    # Cleanup
    os.unlink(path)


def test_set_cycle_median_daily_creates_projection(test_db):
    """Test that set_cycle_median creates projection with correct math"""
    service = CycleService(test_db)

    result = service.set_cycle_median(
        symbol='TEST',
        timeframe='DAILY',
        median_label='2025-12-15',
        cycle_length_bars=35
    )

    assert result['status'] == 'success'
    assert result['symbol'] == 'TEST'
    assert result['timeframe'] == 'DAILY'
    assert result['version'] == 1

    # Verify window math (±3 from median)
    indices = result['indices']['td']
    assert indices['median'] == 14  # td_index for 2025-12-15
    assert indices['start'] == 11  # median - 3
    assert indices['end'] == 17  # median + 3

    # Verify exactly one projection exists
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM cycle_projections
        WHERE instrument_id = 1 AND timeframe = 'DAILY'
    """)
    count = cursor.fetchone()[0]
    assert count == 1
    conn.close()


def test_set_cycle_median_weekly_uses_tw_indices(test_db):
    """Test that WEEKLY cycles use TW indices, not TD"""
    service = CycleService(test_db)

    result = service.set_cycle_median(
        symbol='TEST',
        timeframe='WEEKLY',
        median_label='2025-12-29',  # Later date to avoid clamping
        cycle_length_bars=36
    )

    assert result['status'] == 'success'
    assert result['timeframe'] == 'WEEKLY'

    # Verify TW indices are used, not TD
    assert result['indices']['tw'] is not None
    assert result['indices']['td'] is None

    # Verify window math (with clamping for early dates)
    indices = result['indices']['tw']
    expected_start = max(0, indices['median'] - 3)  # Clamped to 0 if negative
    assert indices['start'] == expected_start
    assert indices['end'] == indices['median'] + 3

    # Verify projection has TW fields set, not TD
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT median_tw_index, median_td_index
        FROM cycle_projections
        WHERE instrument_id = 1 AND timeframe = 'WEEKLY'
    """)
    row = cursor.fetchone()
    assert row[0] is not None  # tw_index set
    assert row[1] is None  # td_index not set
    conn.close()


def test_no_duplicate_projections_on_rebuild(test_db):
    """Test that rebuilding doesn't create duplicates"""
    service = CycleService(test_db)

    # Set median twice with REPLACE mode (should update existing, not create new version)
    service.set_cycle_median('TEST', 'DAILY', '2025-12-15', versioning='REPLACE')
    service.set_cycle_median('TEST', 'DAILY', '2025-12-15', versioning='REPLACE')  # Same again

    # Should still have only 1 projection (same version updated)
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM cycle_projections
        WHERE instrument_id = 1 AND timeframe = 'DAILY' AND k = 0
    """)
    count = cursor.fetchone()[0]
    assert count == 1

    # And only 1 spec (v1)
    cursor.execute("""
        SELECT COUNT(*)
        FROM cycle_specs
        WHERE instrument_id = 1 AND timeframe = 'DAILY'
    """)
    spec_count = cursor.fetchone()[0]
    assert spec_count == 1

    conn.close()


def test_version_bump_creates_new_projection(test_db):
    """Test that BUMP versioning creates new projection and supersedes old"""
    service = CycleService(test_db)

    # Set v1
    result1 = service.set_cycle_median(
        'TEST', 'DAILY', '2025-12-15',
        versioning='BUMP'
    )
    assert result1['version'] == 1

    # Bump to v2
    result2 = service.set_cycle_median(
        'TEST', 'DAILY', '2025-12-20',
        versioning='BUMP'
    )
    assert result2['version'] == 2

    # Verify v1 is SUPERSEDED, v2 is ACTIVE
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT status FROM cycle_specs
        WHERE instrument_id = 1 AND timeframe = 'DAILY' AND version = 1
    """)
    v1_status = cursor.fetchone()[0]
    assert v1_status == 'SUPERSEDED'

    cursor.execute("""
        SELECT status FROM cycle_specs
        WHERE instrument_id = 1 AND timeframe = 'DAILY' AND version = 2
    """)
    v2_status = cursor.fetchone()[0]
    assert v2_status == 'ACTIVE'

    conn.close()


def test_validation_catches_tampered_projection(test_db):
    """Test that validate_cycles catches manually tampered data"""
    service = CycleService(test_db)

    # Create valid projection
    service.set_cycle_median('TEST', 'DAILY', '2025-12-15')

    conn = sqlite3.connect(test_db)

    # Tamper with projection indices
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE cycle_projections
        SET core_start_td_index = 999
        WHERE instrument_id = 1 AND timeframe = 'DAILY'
    """)
    conn.commit()

    # Validation should fail
    with pytest.raises(CycleValidationError) as exc_info:
        validate_cycles(conn, symbol='TEST')

    assert 'core_start_td_index mismatch' in str(exc_info.value)

    conn.close()


def test_validation_catches_null_labels(test_db):
    """Test that validate_cycles catches NULL label columns"""
    service = CycleService(test_db)

    service.set_cycle_median('TEST', 'DAILY', '2025-12-15')

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Tamper: set label to NULL
    cursor.execute("""
        UPDATE cycle_projections
        SET core_start_label = NULL
        WHERE instrument_id = 1 AND timeframe = 'DAILY'
    """)
    conn.commit()

    # Validation should fail
    with pytest.raises(CycleValidationError) as exc_info:
        validate_cycles(conn, symbol='TEST')

    assert 'NULL label columns' in str(exc_info.value)

    conn.close()


def test_validation_catches_cross_calendar_contamination(test_db):
    """Test that validate_cycles catches DAILY with TW indices"""
    service = CycleService(test_db)

    service.set_cycle_median('TEST', 'DAILY', '2025-12-15')

    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Tamper: set TW index on DAILY projection
    cursor.execute("""
        UPDATE cycle_projections
        SET median_tw_index = 5
        WHERE instrument_id = 1 AND timeframe = 'DAILY'
    """)
    conn.commit()

    # Validation should fail
    with pytest.raises(CycleValidationError) as exc_info:
        validate_cycles(conn, symbol='TEST')

    assert 'median_tw_index is set (must be NULL for DAILY)' in str(exc_info.value)

    conn.close()


def test_update_cycle_defaults_rebuilds(test_db):
    """Test that updating defaults triggers rebuild"""
    service = CycleService(test_db)

    # Create initial cycle
    result1 = service.set_cycle_median('TEST', 'DAILY', '2025-12-15')
    initial_start = result1['indices']['td']['start']
    assert initial_start == 11  # median 14 - 3

    # Update to wider window (±5 instead of ±3)
    service.add_or_update_cycle_defaults(
        'TEST', 'DAILY',
        window_minus_bars=5,
        window_plus_bars=5
    )

    # Get updated info
    info = service.get_cycle_info('TEST', 'DAILY')
    assert info['window_minus_bars'] == 5

    # Verify projection was rebuilt with new window
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT core_start_td_index, median_td_index, core_end_td_index
        FROM cycle_projections
        WHERE instrument_id = 1 AND timeframe = 'DAILY' AND k = 0
    """)
    start, median, end = cursor.fetchone()
    assert start == median - 5
    assert end == median + 5
    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
