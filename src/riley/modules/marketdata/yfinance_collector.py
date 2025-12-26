"""Yahoo Finance data collector using yfinance library"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_ohlcv(
    symbol: str,
    start_date: str,
    end_date: str,
    max_retries: int = 3,
    retry_delay: int = 2
) -> Optional[pd.DataFrame]:
    """
    Collect OHLCV data for a single symbol from Yahoo Finance.

    Args:
        symbol: Ticker symbol (e.g., 'SPY')
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_retries: Maximum number of retry attempts
        retry_delay: Delay in seconds between retries

    Returns:
        DataFrame with columns: date, symbol, open, high, low, close, adj_close, volume
        Returns None if collection fails
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching {symbol} from {start_date} to {end_date} (attempt {attempt + 1}/{max_retries})")

            # Download data using yfinance
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval='1d')

            if df.empty:
                logger.warning(f"No data returned for {symbol}")
                return None

            # Reset index to get date as column
            df = df.reset_index()

            # Rename columns to match our schema
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })

            # Add adj_close (use Close if Adj Close not available)
            if 'Adj Close' in df.columns:
                df['adj_close'] = df['Adj Close']
            else:
                df['adj_close'] = df['close']

            # Add symbol column
            df['symbol'] = symbol

            # Select only required columns
            df = df[['date', 'symbol', 'open', 'high', 'low', 'close', 'adj_close', 'volume']]

            # Convert date to string format (YYYY-MM-DD)
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

            logger.info(f"✅ Successfully fetched {len(df)} bars for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            else:
                logger.error(f"❌ Failed to fetch {symbol} after {max_retries} attempts")
                return None


def backfill_symbols(
    symbols: List[str],
    lookback_days: int = 730,  # Default 2 years
    end_date: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """
    Backfill historical data for multiple symbols.

    Args:
        symbols: List of ticker symbols
        lookback_days: Number of days to look back (default 730 = ~2 years)
        end_date: End date in YYYY-MM-DD format (default: today)

    Returns:
        Dictionary mapping symbol -> DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')

    start_date = (datetime.strptime(end_date, '%Y-%m-%d') - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

    logger.info(f"Backfilling {len(symbols)} symbols from {start_date} to {end_date}")

    results = {}
    for symbol in symbols:
        df = collect_ohlcv(symbol, start_date, end_date)
        if df is not None and not df.empty:
            results[symbol] = df
        time.sleep(0.5)  # Rate limiting between symbols

    logger.info(f"✅ Backfill complete: {len(results)}/{len(symbols)} symbols successful")
    return results


def fetch_daily_update(
    symbols: List[str],
    lookback_days: int = 10  # Overlap window for safety
) -> Dict[str, pd.DataFrame]:
    """
    Fetch recent data for daily updates.

    Args:
        symbols: List of ticker symbols
        lookback_days: Number of days to look back (default 10 for overlap)

    Returns:
        Dictionary mapping symbol -> DataFrame
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')

    logger.info(f"Daily update: fetching {len(symbols)} symbols from {start_date} to {end_date}")

    results = {}
    for symbol in symbols:
        df = collect_ohlcv(symbol, start_date, end_date)
        if df is not None and not df.empty:
            results[symbol] = df
        time.sleep(0.5)  # Rate limiting

    logger.info(f"✅ Daily update complete: {len(results)}/{len(symbols)} symbols successful")
    return results


# Define RRG sector universe
RRG_SECTOR_UNIVERSE = [
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
