#!/usr/bin/env python3
"""
Add equity and ETF instruments to Riley database.
"""

import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "db" / "riley.sqlite"

# Stock names (manually curated)
STOCK_NAMES = {
    "AAPL": "Apple Inc.",
    "AMAT": "Applied Materials Inc.",
    "AMD": "Advanced Micro Devices Inc.",
    "AMGN": "Amgen Inc.",
    "AMZN": "Amazon.com Inc.",
    "AVGO": "Broadcom Inc.",
    "BA": "Boeing Company",
    "BABA": "Alibaba Group Holding Ltd",
    "BIDU": "Baidu Inc.",
    "CAT": "Caterpillar Inc.",
    "COST": "Costco Wholesale Corporation",
    "CRM": "Salesforce Inc.",
    "CVX": "Chevron Corporation",
    "DE": "Deere & Company",
    "DIS": "Walt Disney Company",
    "FCX": "Freeport-McMoRan Inc.",
    "FDX": "FedEx Corporation",
    "FSLR": "First Solar Inc.",
    "GOOGL": "Alphabet Inc.",
    "GS": "Goldman Sachs Group Inc.",
    "HD": "Home Depot Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "LUV": "Southwest Airlines Co.",
    "LVS": "Las Vegas Sands Corp.",
    "MCD": "McDonald's Corporation",
    "META": "Meta Platforms Inc.",
    "MS": "Morgan Stanley",
    "MSFT": "Microsoft Corporation",
    "MU": "Micron Technology Inc.",
    "NEM": "Newmont Corporation",
    "NFLX": "Netflix Inc.",
    "NKE": "Nike Inc.",
    "NVDA": "NVIDIA Corporation",
    "ORCL": "Oracle Corporation",
    "PAAS": "Pan American Silver Corp.",
    "PEP": "PepsiCo Inc.",
    "PYPL": "PayPal Holdings Inc.",
    "SBUX": "Starbucks Corporation",
    "TMUS": "T-Mobile US Inc.",
    "TOL": "Toll Brothers Inc.",
    "TSLA": "Tesla Inc.",
    "UAL": "United Airlines Holdings Inc.",
    "UBER": "Uber Technologies Inc.",
    "V": "Visa Inc.",
    "WMT": "Walmart Inc.",
    "WYNN": "Wynn Resorts Ltd.",
    "XOM": "Exxon Mobil Corporation",
}

ETF_NAMES = {
    "SMH": "VanEck Semiconductor ETF",
    "XBI": "SPDR S&P Biotech ETF",
    "XLE": "Energy Select Sector SPDR Fund",
    "XLF": "Financial Select Sector SPDR Fund",
    "XLI": "Industrial Select Sector SPDR Fund",
    "XLK": "Technology Select Sector SPDR Fund",
    "XLP": "Consumer Staples Select Sector SPDR Fund",
    "XRT": "SPDR S&P Retail ETF",
    "EEM": "iShares MSCI Emerging Markets ETF",
    "FEZ": "SPDR EURO STOXX 50 ETF",
    "FXI": "iShares China Large-Cap ETF",
    "GDX": "VanEck Gold Miners ETF",
}

def add_instruments():
    """Add all equity and ETF instruments."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("="*70)
    print("ADDING EQUITY AND ETF INSTRUMENTS")
    print("="*70)

    # Add stocks
    print(f"\n📊 Adding {len(STOCK_NAMES)} stocks...")
    added_stocks = 0
    skipped_stocks = 0

    for symbol, name in STOCK_NAMES.items():
        # Check if already exists
        cursor.execute("SELECT instrument_id FROM instruments WHERE canonical_symbol = ?", (symbol,))
        if cursor.fetchone():
            print(f"  ⏭ {symbol:6} - already exists")
            skipped_stocks += 1
            continue

        # Insert stock
        cursor.execute("""
            INSERT INTO instruments (
                symbol, canonical_symbol, name, role,
                instrument_type, group_name, sector,
                active, sort_key
            ) VALUES (?, ?, ?, 'CANONICAL', 'STOCK', 'STOCKS', 'UNCLASSIFIED', 1, 2000)
        """, (symbol, symbol, name))

        print(f"  ✓ {symbol:6} - {name}")
        added_stocks += 1

    # Add ETFs
    print(f"\n📊 Adding {len(ETF_NAMES)} ETFs...")
    added_etfs = 0
    skipped_etfs = 0

    for symbol, name in ETF_NAMES.items():
        # Check if already exists
        cursor.execute("SELECT instrument_id FROM instruments WHERE canonical_symbol = ?", (symbol,))
        if cursor.fetchone():
            print(f"  ⏭ {symbol:6} - already exists")
            skipped_etfs += 1
            continue

        # Insert ETF
        cursor.execute("""
            INSERT INTO instruments (
                symbol, canonical_symbol, name, role,
                instrument_type, group_name, sector,
                active, sort_key
            ) VALUES (?, ?, ?, 'CANONICAL', 'ETF', 'ETFS', 'UNCLASSIFIED', 1, 3000)
        """, (symbol, symbol, name))

        print(f"  ✓ {symbol:6} - {name}")
        added_etfs += 1

    conn.commit()
    conn.close()

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"  Stocks: {added_stocks} added, {skipped_stocks} skipped")
    print(f"  ETFs:   {added_etfs} added, {skipped_etfs} skipped")
    print(f"  Total:  {added_stocks + added_etfs} instruments added")
    print("="*70)


if __name__ == "__main__":
    add_instruments()
