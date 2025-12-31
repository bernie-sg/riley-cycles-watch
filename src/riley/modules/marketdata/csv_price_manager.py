#!/usr/bin/env python3
"""
Shared CSV Price Data Manager
Used by both RRG and Cycles Detector
Stores price history in data/price_history/ folder
"""

import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_price_history_dir() -> Path:
    """Get path to shared price history directory"""
    project_root = Path(__file__).parent.parent.parent.parent.parent
    price_dir = project_root / "data" / "price_history"
    price_dir.mkdir(parents=True, exist_ok=True)
    return price_dir


def get_price_data(symbol: str) -> tuple[np.ndarray, pd.DataFrame]:
    """
    Get price data for a symbol from CSV files.
    Downloads if not exists, updates if outdated.

    Args:
        symbol: Ticker symbol (e.g., 'SPY')

    Returns:
        Tuple of (prices array, DataFrame with Date and Close columns)
    """
    symbol = symbol.upper()
    price_dir = get_price_history_dir()
    csv_file = price_dir / f"{symbol.lower()}_history.csv"

    if not csv_file.exists():
        logger.info(f"📥 No history file for {symbol}. Downloading full history...")
        _download_full_history(symbol, csv_file)
    else:
        logger.info(f"✓ Found existing history file for {symbol}")
        _update_if_needed(symbol, csv_file)

    # Load CSV and return prices
    df = pd.read_csv(csv_file, parse_dates=['Date'])
    prices = df['Close'].values

    logger.info(f"✓ Loaded {len(prices)} bars for {symbol} ({df['Date'].min().date()} to {df['Date'].max().date()})")

    return prices, df


def _download_full_history(symbol: str, csv_file: Path):
    """Download complete history from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='max')

        if df.empty:
            raise ValueError(f"No data returned for {symbol}")

        # Keep only Date and Close
        df = df[['Close']].reset_index()
        # Convert to date objects (strip timezone and time)
        df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None).dt.date

        # Save to CSV
        df.to_csv(csv_file, index=False)
        logger.info(f"✓ Downloaded {len(df)} bars for {symbol}")

    except Exception as e:
        raise ValueError(f"Failed to download {symbol}: {str(e)}")


def _update_if_needed(symbol: str, csv_file: Path):
    """Check if data is current and update if needed"""
    df = pd.read_csv(csv_file)
    df['Date'] = pd.to_datetime(df['Date'])
    last_date = df['Date'].max()

    if hasattr(last_date, 'date'):
        last_date = last_date.date()

    today = datetime.now().date()

    # Check if we're missing recent data (more than 1 day old)
    if last_date < today - timedelta(days=1):
        logger.info(f"📥 {symbol} data is outdated (last: {last_date}). Updating...")

        # Download from day after last_date to today
        ticker = yf.Ticker(symbol)
        start_date = last_date + timedelta(days=1)
        new_data = ticker.history(start=start_date.strftime('%Y-%m-%d'))

        if len(new_data) > 0:
            # Keep only Date and Close
            new_data = new_data[['Close']].reset_index()
            new_data['Date'] = pd.to_datetime(new_data['Date']).dt.tz_localize(None).dt.date

            # Ensure existing df also has date objects
            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None).dt.date

            # Append to existing data
            df = pd.concat([df, new_data], ignore_index=True)
            df = df.drop_duplicates(subset=['Date'], keep='last')
            df = df.sort_values('Date').reset_index(drop=True)

            # Save updated CSV
            df.to_csv(csv_file, index=False)
            logger.info(f"✓ Added {len(new_data)} new bars for {symbol} (now {len(df)} total)")
        else:
            logger.info(f"✓ No new data available for {symbol}")
    else:
        logger.info(f"✓ {symbol} data is current (last: {last_date})")


def update_rrg_universe():
    """Update all symbols in the RRG universe"""
    RRG_SYMBOLS = [
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

    logger.info(f"Updating {len(RRG_SYMBOLS)} RRG symbols...")

    for symbol in RRG_SYMBOLS:
        try:
            get_price_data(symbol)
        except Exception as e:
            logger.error(f"Failed to update {symbol}: {e}")

    logger.info("✅ RRG universe update complete")


def load_rrg_data() -> pd.DataFrame:
    """
    Load all RRG symbols from CSV files into a single DataFrame.
    Returns DataFrame with columns: date, symbol, open, high, low, close, volume
    """
    RRG_SYMBOLS = [
        'SPY', 'XLK', 'XLY', 'XLC', 'XLV', 'XLF',
        'XLE', 'XLI', 'XLP', 'XLU', 'XLB', 'XLRE'
    ]

    all_data = []

    for symbol in RRG_SYMBOLS:
        try:
            _, df = get_price_data(symbol)

            # Add required columns
            df['symbol'] = symbol
            df = df.rename(columns={'Date': 'date', 'Close': 'close'})

            # Add placeholder OHLV columns (we only track Close in CSV)
            df['open'] = df['close']
            df['high'] = df['close']
            df['low'] = df['close']
            df['volume'] = 0

            df = df[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]

            all_data.append(df)

        except Exception as e:
            logger.error(f"Failed to load {symbol}: {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined = combined.sort_values(['date', 'symbol']).reset_index(drop=True)
        return combined
    else:
        return pd.DataFrame(columns=['date', 'symbol', 'open', 'high', 'low', 'close', 'volume'])


if __name__ == '__main__':
    # Test the price manager
    print("Testing CSV Price Manager")
    print("=" * 50)

    prices, df = get_price_data('SPY')

    print(f"\nData summary:")
    print(f"  Symbol: SPY")
    print(f"  Total bars: {len(prices)}")
    print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"  Latest price: ${prices[-1]:.2f}")
