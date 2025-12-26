"""Database storage operations for market data"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_path() -> Path:
    """Get path to Riley SQLite database"""
    project_root = Path(__file__).parent.parent.parent.parent.parent
    return project_root / "db" / "riley.sqlite"


def store_price_bars(df: pd.DataFrame, db_path: Optional[Path] = None) -> int:
    """
    Store price bars in database using upsert (idempotent).

    Args:
        df: DataFrame with columns: date, symbol, open, high, low, close, adj_close, volume
        db_path: Path to SQLite database (default: auto-detect)

    Returns:
        Number of rows upserted
    """
    if db_path is None:
        db_path = get_db_path()

    if df.empty:
        logger.warning("Empty DataFrame provided, nothing to store")
        return 0

    # Validate required columns
    required_cols = ['date', 'symbol', 'open', 'high', 'low', 'close']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Add optional columns if missing
    if 'adj_close' not in df.columns:
        df['adj_close'] = df['close']
    if 'volume' not in df.columns:
        df['volume'] = None

    # Add timestamps
    now = datetime.now().isoformat()
    df['created_at'] = now
    df['updated_at'] = now
    df['source'] = 'yfinance'

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Upsert query (INSERT ON CONFLICT DO UPDATE)
    upsert_sql = """
        INSERT INTO price_bars_daily (
            symbol, date, open, high, low, close, adj_close, volume, source, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, date) DO UPDATE SET
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            close = excluded.close,
            adj_close = excluded.adj_close,
            volume = excluded.volume,
            updated_at = excluded.updated_at
    """

    # Prepare data for insertion
    rows = df[[
        'symbol', 'date', 'open', 'high', 'low', 'close',
        'adj_close', 'volume', 'source', 'created_at', 'updated_at'
    ]].values.tolist()

    # Execute upsert
    cursor.executemany(upsert_sql, rows)
    conn.commit()

    rows_affected = cursor.rowcount
    conn.close()

    logger.info(f"✅ Upserted {rows_affected} price bars to database")
    return rows_affected


def get_latest_date(symbol: str, db_path: Optional[Path] = None) -> Optional[str]:
    """
    Get the latest date for which we have data for a symbol.

    Args:
        symbol: Ticker symbol
        db_path: Path to SQLite database (default: auto-detect)

    Returns:
        Latest date as string (YYYY-MM-DD) or None if no data exists
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT MAX(date) FROM price_bars_daily WHERE symbol = ?",
        (symbol,)
    )
    result = cursor.fetchone()
    conn.close()

    return result[0] if result and result[0] else None


def get_date_range(symbol: str, db_path: Optional[Path] = None) -> tuple:
    """
    Get the date range for a symbol in the database.

    Args:
        symbol: Ticker symbol
        db_path: Path to SQLite database (default: auto-detect)

    Returns:
        Tuple of (min_date, max_date) or (None, None) if no data
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT MIN(date), MAX(date) FROM price_bars_daily WHERE symbol = ?",
        (symbol,)
    )
    result = cursor.fetchone()
    conn.close()

    return (result[0], result[1]) if result else (None, None)


def get_symbol_count(db_path: Optional[Path] = None) -> int:
    """
    Get count of distinct symbols in database.

    Args:
        db_path: Path to SQLite database (default: auto-detect)

    Returns:
        Number of distinct symbols
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(DISTINCT symbol) FROM price_bars_daily")
    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 0


def get_bar_count(symbol: Optional[str] = None, db_path: Optional[Path] = None) -> int:
    """
    Get count of price bars in database.

    Args:
        symbol: Optional ticker symbol to filter by
        db_path: Path to SQLite database (default: auto-detect)

    Returns:
        Number of price bars
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    if symbol:
        cursor.execute("SELECT COUNT(*) FROM price_bars_daily WHERE symbol = ?", (symbol,))
    else:
        cursor.execute("SELECT COUNT(*) FROM price_bars_daily")

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 0
