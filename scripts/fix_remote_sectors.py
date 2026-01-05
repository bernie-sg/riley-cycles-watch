#!/usr/bin/env python3
"""Fix instrument sectors - run this on remote server"""
import sqlite3
import sys
from pathlib import Path

# Detect if running on remote or local
if Path('/home/raysudo/riley-cycles').exists():
    DB_PATH = '/home/raysudo/riley-cycles/db/riley.sqlite'
else:
    DB_PATH = str(Path(__file__).parent.parent / 'db' / 'riley.sqlite')

print(f"Using database: {DB_PATH}")

# Proper sector mappings
instruments = [
    # FUTURES
    ("ES", "INDICES"), ("NQ", "INDICES"), ("RTY", "INDICES"),
    ("CL", "ENERGY"), ("NG", "ENERGY"),
    ("GC", "METALS"), ("SI", "METALS"), ("PL", "METALS"), ("HG", "METALS"),
    ("ZC", "AGRICULTURE"), ("ZS", "AGRICULTURE"), ("ZW", "AGRICULTURE"),
    ("ZB", "FIXED_INCOME"),

    # FX
    ("DXY", "CURRENCIES"), ("EURUSD", "CURRENCIES"), ("GBPUSD", "CURRENCIES"),
    ("USDJPY", "CURRENCIES"), ("AUDUSD", "CURRENCIES"),

    # CRYPTO
    ("BTC", "DIGITAL_ASSETS"),

    # EQUITY - Technology
    ("AAPL", "TECHNOLOGY"), ("GOOGL", "TECHNOLOGY"), ("MSFT", "TECHNOLOGY"),
    ("META", "TECHNOLOGY"), ("NVDA", "TECHNOLOGY"), ("CRM", "TECHNOLOGY"),
    ("ORCL", "TECHNOLOGY"), ("AVGO", "TECHNOLOGY"), ("AMD", "TECHNOLOGY"),
    ("AMAT", "TECHNOLOGY"), ("MU", "TECHNOLOGY"), ("TMUS", "TECHNOLOGY"),
    ("NFLX", "TECHNOLOGY"), ("BIDU", "TECHNOLOGY"), ("BABA", "TECHNOLOGY"),

    # EQUITY - Financials
    ("JPM", "FINANCIALS"), ("GS", "FINANCIALS"), ("MS", "FINANCIALS"),
    ("V", "FINANCIALS"), ("PYPL", "FINANCIALS"),

    # EQUITY - Consumer Discretionary
    ("AMZN", "CONSUMER_DISCRETIONARY"), ("DIS", "CONSUMER_DISCRETIONARY"),
    ("SBUX", "CONSUMER_DISCRETIONARY"), ("MCD", "CONSUMER_DISCRETIONARY"),
    ("NKE", "CONSUMER_DISCRETIONARY"), ("TSLA", "CONSUMER_DISCRETIONARY"),
    ("HD", "CONSUMER_DISCRETIONARY"), ("TOL", "CONSUMER_DISCRETIONARY"),
    ("LVS", "CONSUMER_DISCRETIONARY"), ("WYNN", "CONSUMER_DISCRETIONARY"),
    ("UBER", "CONSUMER_DISCRETIONARY"), ("UAL", "CONSUMER_DISCRETIONARY"),
    ("LUV", "CONSUMER_DISCRETIONARY"),

    # EQUITY - Consumer Staples
    ("WMT", "CONSUMER_STAPLES"), ("COST", "CONSUMER_STAPLES"), ("PEP", "CONSUMER_STAPLES"),

    # EQUITY - Energy
    ("XOM", "ENERGY"), ("CVX", "ENERGY"), ("FCX", "ENERGY"), ("FSLR", "ENERGY"),

    # EQUITY - Industrials
    ("CAT", "INDUSTRIALS"), ("BA", "INDUSTRIALS"), ("DE", "INDUSTRIALS"), ("FDX", "INDUSTRIALS"),

    # EQUITY - Materials
    ("NEM", "MATERIALS"), ("PAAS", "MATERIALS"),

    # EQUITY - Healthcare
    ("AMGN", "HEALTHCARE"),

    # ETF
    ("XLE", "ENERGY"), ("XLF", "FINANCIALS"), ("XLI", "INDUSTRIALS"),
    ("XLK", "TECHNOLOGY"), ("XLP", "CONSUMER_STAPLES"), ("SMH", "TECHNOLOGY"),
    ("XBI", "HEALTHCARE"), ("XRT", "CONSUMER_DISCRETIONARY"),
    ("EEM", "INTERNATIONAL"), ("FEZ", "INTERNATIONAL"), ("FXI", "INTERNATIONAL"),
    ("GDX", "METALS"),
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

updated = 0
for symbol, sector in instruments:
    cursor.execute("UPDATE instruments SET sector = ? WHERE symbol = ?", (sector, symbol))
    if cursor.rowcount > 0:
        print(f"  {symbol} → {sector}")
        updated += 1

conn.commit()
conn.close()

print(f"\n✅ Updated {updated} instruments with proper sectors")
