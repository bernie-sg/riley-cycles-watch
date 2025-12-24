"""
Riley Cycles Watch - Configuration
Centralized configuration for database path and settings.
"""
import os
from pathlib import Path
from datetime import datetime


def get_db_path() -> Path:
    """
    Get the absolute path to the riley.sqlite database.

    Priority order:
    1. Environment variable RILEY_DB_PATH if set
    2. Project root /db/riley.sqlite (default)

    Returns:
        Path: Absolute path to riley.sqlite
    """
    # Check for environment variable override
    env_path = os.environ.get('RILEY_DB_PATH')
    if env_path:
        return Path(env_path).resolve()

    # Default: project_root/db/riley.sqlite
    # This file is at: project_root/app/config.py
    project_root = Path(__file__).parent.parent
    return (project_root / "db" / "riley.sqlite").resolve()


def get_db_info() -> dict:
    """
    Get database diagnostic information.

    Returns:
        dict: Database info including path, exists, modified time, latest scan
    """
    db_path = get_db_path()

    info = {
        'path': str(db_path),
        'exists': db_path.exists(),
        'modified': None,
        'latest_scan': None,
        'instrument_count': None,
        'es_notes_count': None,
        'es_latest_note': None
    }

    if db_path.exists():
        # Get file modified time
        mtime = datetime.fromtimestamp(db_path.stat().st_mtime)
        info['modified'] = mtime.strftime('%Y-%m-%d %H:%M:%S')

        # Query database for stats
        import sqlite3
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get latest scan label
            cursor.execute("""
                SELECT scan_td_label
                FROM daily_scan_runs
                ORDER BY scan_td_label DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                info['latest_scan'] = row['scan_td_label']

            # Get instrument count
            cursor.execute("SELECT COUNT(*) as cnt FROM instruments WHERE role='CANONICAL' AND active=1")
            row = cursor.fetchone()
            if row:
                info['instrument_count'] = row['cnt']

            # Get ES instrument_id
            cursor.execute("SELECT instrument_id FROM instruments WHERE symbol='ES' AND role='CANONICAL'")
            row = cursor.fetchone()
            if row:
                es_id = row['instrument_id']

                # Get ES notes count
                cursor.execute("SELECT COUNT(*) as cnt FROM desk_notes WHERE instrument_id=?", (es_id,))
                row = cursor.fetchone()
                if row:
                    info['es_notes_count'] = row['cnt']

                # Get ES latest note date
                cursor.execute("""
                    SELECT asof_td_label
                    FROM desk_notes
                    WHERE instrument_id=?
                    ORDER BY asof_td_label DESC
                    LIMIT 1
                """, (es_id,))
                row = cursor.fetchone()
                if row:
                    info['es_latest_note'] = row['asof_td_label']

            conn.close()
        except Exception as e:
            info['error'] = str(e)

    return info
