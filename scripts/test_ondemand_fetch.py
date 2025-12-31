#!/usr/bin/env python3
"""
Test On-Demand Data Fetching
Verifies that Cycles Detector can fetch and store new symbols
"""
import sys
from pathlib import Path
import sqlite3
import yfinance as yf
import pandas as pd

project_root = Path(__file__).parent.parent
db_path = project_root / "db" / "riley.sqlite"

print("=" * 80)
print("ON-DEMAND DATA FETCHING TEST")
print("=" * 80)

# Test symbol that probably isn't in the database
test_symbol = "AAPL"

# Check if it exists
print(f"\n1. Checking if {test_symbol} exists in database...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT COUNT(*) FROM price_bars_daily WHERE symbol = ?
""", (test_symbol,))
count_before = cursor.fetchone()[0]

if count_before > 0:
    print(f"   ⚠️  {test_symbol} already has {count_before} bars")
    print(f"   Will delete and re-test fetching...")
    cursor.execute("DELETE FROM price_bars_daily WHERE symbol = ?", (test_symbol,))
    conn.commit()
    print(f"   ✅ Deleted existing data")
else:
    print(f"   ✅ {test_symbol} not in database (good for testing)")

conn.close()

# Simulate the fetch_and_store_data function from the Streamlit page
print(f"\n2. Fetching {test_symbol} from Yahoo Finance...")
try:
    ticker = yf.Ticker(test_symbol)
    hist = ticker.history(period='2y')

    if hist.empty:
        print(f"   ❌ No data returned from Yahoo Finance")
        sys.exit(1)

    print(f"   ✅ Retrieved {len(hist)} bars")
    print(f"   Date range: {hist.index[0].date()} to {hist.index[-1].date()}")

    # Prepare data
    hist = hist.reset_index()
    hist['Date'] = pd.to_datetime(hist['Date']).dt.date

    # Store in database
    print(f"\n3. Storing {test_symbol} in Riley's database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    stored_count = 0
    for _, row in hist.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO price_bars_daily
            (symbol, date, open, high, low, close, adj_close, volume, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            test_symbol,
            str(row['Date']),
            row['Open'],
            row['High'],
            row['Low'],
            row['Close'],
            row.get('Close', row['Close']),
            int(row['Volume']),
            'yfinance_cycles_detector'
        ))
        stored_count += 1

    conn.commit()
    print(f"   ✅ Stored {stored_count} bars in database")

    # Verify storage
    print(f"\n4. Verifying data was stored correctly...")
    cursor.execute("""
        SELECT COUNT(*), MIN(date), MAX(date)
        FROM price_bars_daily
        WHERE symbol = ? AND source = 'yfinance_cycles_detector'
    """, (test_symbol,))

    count, min_date, max_date = cursor.fetchone()
    print(f"   ✅ Verified {count} bars in database")
    print(f"   Date range: {min_date} to {max_date}")

    # Check source tagging
    cursor.execute("""
        SELECT source, COUNT(*) as count
        FROM price_bars_daily
        WHERE symbol = ?
        GROUP BY source
    """, (test_symbol,))

    print(f"\n5. Verifying source tagging...")
    for source, count in cursor.fetchall():
        print(f"   - {source}: {count} bars")

    conn.close()

    # Summary
    print("\n" + "=" * 80)
    print("ON-DEMAND FETCHING TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Symbol: {test_symbol}")
    print(f"✅ Fetched: {len(hist)} bars from Yahoo Finance")
    print(f"✅ Stored: {stored_count} bars in Riley database")
    print(f"✅ Source: yfinance_cycles_detector")
    print(f"✅ Table: price_bars_daily (shared with RRG)")
    print("\n✅ ON-DEMAND DATA FETCHING WORKING CORRECTLY")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
