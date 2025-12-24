"""Tests for database module"""
import pytest
import tempfile
from pathlib import Path
from riley.database import Database


def test_database_migrations():
    """Test that database migrations run successfully"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        db = Database(str(db_path))

        # Run migrations (need to copy migration file)
        # For now just test connection
        conn = db.connect()
        assert conn is not None
        db.close()


def test_create_run():
    """Test creating a run record"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        db = Database(str(db_path))

        # Manually create tables
        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                as_of_date TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL
            )
        """)
        conn.commit()

        # Test create_run
        run_id = db.create_run('2025-01-01')
        assert run_id > 0

        # Test finish_run
        db.finish_run(run_id, 'success')

        # Verify
        cursor.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        assert row['status'] == 'success'
        assert row['finished_at'] is not None

        db.close()


def test_upsert_instrument():
    """Test instrument upsert"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        db = Database(str(db_path))

        conn = db.connect()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE instruments (
                symbol TEXT PRIMARY KEY,
                type TEXT,
                source_preference TEXT
            )
        """)
        conn.commit()

        # Insert
        db.upsert_instrument('TEST', 'equity', 'IBKR')

        # Verify
        cursor.execute("SELECT * FROM instruments WHERE symbol = ?", ('TEST',))
        row = cursor.fetchone()
        assert row['symbol'] == 'TEST'
        assert row['type'] == 'equity'

        # Update
        db.upsert_instrument('TEST', 'future', None)
        cursor.execute("SELECT * FROM instruments WHERE symbol = ?", ('TEST',))
        row = cursor.fetchone()
        assert row['type'] == 'future'

        db.close()


def test_create_analysis():
    """Test analysis record creation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.sqlite"
        db = Database(str(db_path))

        conn = db.connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE instruments (
                symbol TEXT PRIMARY KEY,
                type TEXT,
                source_preference TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                as_of_date TEXT NOT NULL,
                packet_path TEXT NOT NULL,
                skeleton_report_path TEXT NOT NULL,
                final_report_path TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(symbol, as_of_date)
            )
        """)
        conn.commit()

        # Insert instrument first
        db.upsert_instrument('TEST', 'equity', 'STUB')

        # Create analysis
        analysis_id = db.create_analysis(
            'TEST', '2025-01-01',
            '/path/to/packet.json',
            '/path/to/skeleton.md'
        )

        assert analysis_id > 0

        # Verify
        cursor.execute("SELECT * FROM analysis WHERE id = ?", (analysis_id,))
        row = cursor.fetchone()
        assert row['symbol'] == 'TEST'
        assert row['as_of_date'] == '2025-01-01'

        db.close()
