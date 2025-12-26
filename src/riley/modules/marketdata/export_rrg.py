"""Export price data to RRG-compatible CSV format"""
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_path() -> Path:
    """Get path to Riley SQLite database"""
    project_root = Path(__file__).parent.parent.parent.parent.parent
    return project_root / "db" / "riley.sqlite"


def export_rrg_csv(
    output_path: str,
    symbols: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Optional[Path] = None
) -> str:
    """
    Export price data to CSV in Mode A format for RRG app.

    Mode A format columns: date, symbol, open, high, low, close, volume

    Args:
        output_path: Path to output CSV file
        symbols: List of symbols to export (default: all symbols)
        start_date: Start date filter (YYYY-MM-DD) (default: all dates)
        end_date: End date filter (YYYY-MM-DD) (default: all dates)
        db_path: Path to SQLite database (default: auto-detect)

    Returns:
        Path to exported CSV file
    """
    if db_path is None:
        db_path = get_db_path()

    # Build query
    query = "SELECT date, symbol, open, high, low, close, volume FROM price_bars_daily"
    conditions = []
    params = []

    if symbols:
        placeholders = ','.join(['?'] * len(symbols))
        conditions.append(f"symbol IN ({placeholders})")
        params.extend(symbols)

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)

    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY date, symbol"

    # Execute query
    logger.info(f"Exporting price data from database...")
    conn = sqlite3.connect(str(db_path))
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    # Validate data
    if df.empty:
        logger.warning("No data to export")
        return output_path

    # Export to CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_path, index=False)

    logger.info(f"✅ Exported {len(df)} rows ({df['symbol'].nunique()} symbols) to {output_path}")
    logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")

    return str(output_path)


def export_rrg_sectors(
    output_path: str,
    lookback_days: int = 365,
    db_path: Optional[Path] = None
) -> str:
    """
    Export RRG sector universe data (SPY + 11 sector ETFs) to CSV.

    Args:
        output_path: Path to output CSV file
        lookback_days: Number of days to include (default: 365)
        db_path: Path to SQLite database (default: auto-detect)

    Returns:
        Path to exported CSV file
    """
    # RRG sector universe
    rrg_symbols = [
        'SPY',   # Benchmark
        'XLK',   # Technology
        'XLY',   # Consumer Discretionary
        'XLC',   # Communication Services
        'XLV',   # Health Care
        'XLF',   # Financials
        'XLE',   # Energy
        'XLI',   # Industrials
        'XLP',   # Consumer Staples
        'XLU',   # Utilities
        'XLB',   # Materials
        'XLRE'   # Real Estate
    ]

    if db_path is None:
        db_path = get_db_path()

    # Calculate start date
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

    logger.info(f"Exporting RRG sector data from {start_date} to {end_date}")

    return export_rrg_csv(
        output_path=output_path,
        symbols=rrg_symbols,
        start_date=start_date,
        end_date=end_date,
        db_path=db_path
    )


def get_export_stats(db_path: Optional[Path] = None) -> dict:
    """
    Get statistics about exportable data.

    Args:
        db_path: Path to SQLite database (default: auto-detect)

    Returns:
        Dictionary with stats
    """
    if db_path is None:
        db_path = get_db_path()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get overall stats
    cursor.execute("""
        SELECT
            COUNT(DISTINCT symbol) as symbol_count,
            COUNT(*) as total_bars,
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM price_bars_daily
    """)
    overall = cursor.fetchone()

    # Get per-symbol stats
    cursor.execute("""
        SELECT
            symbol,
            COUNT(*) as bar_count,
            MIN(date) as min_date,
            MAX(date) as max_date
        FROM price_bars_daily
        GROUP BY symbol
        ORDER BY symbol
    """)
    per_symbol = cursor.fetchall()

    conn.close()

    return {
        'total_symbols': overall[0] if overall else 0,
        'total_bars': overall[1] if overall else 0,
        'date_range': {
            'min': overall[2] if overall else None,
            'max': overall[3] if overall else None
        },
        'symbols': [
            {
                'symbol': row[0],
                'bars': row[1],
                'min_date': row[2],
                'max_date': row[3]
            }
            for row in per_symbol
        ]
    }
