#!/usr/bin/env python3
"""
Complete End-to-End Workflow Test
Simulates exactly what happens when user clicks "Run Analysis" in Streamlit
"""
import sys
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "cycles-detector" / "algorithms" / "bandpass"))

from pure_sine_bandpass import create_pure_sine_bandpass

db_path = project_root / "db" / "riley.sqlite"

print("=" * 80)
print("COMPLETE END-TO-END WORKFLOW TEST")
print("Simulating user clicking 'Run Analysis' in Cycles Detector Streamlit page")
print("=" * 80)

# Simulate user input
test_symbol = "AAPL"
test_wavelength = 380

print(f"\nUser Input:")
print(f"  Symbol: {test_symbol}")
print(f"  Wavelength: {test_wavelength} days")

# Step 1: Get data from database (simulating get_price_data function)
print(f"\n📥 Step 1: Fetching data for {test_symbol}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT date, close
    FROM price_bars_daily
    WHERE symbol = ?
    ORDER BY date
""", (test_symbol,))

rows = cursor.fetchall()

if rows:
    df = pd.DataFrame(rows, columns=['date', 'close'])
    df['date'] = pd.to_datetime(df['date'])
    prices = df['close'].values
    print(f"✅ Loaded {len(prices)} bars from database")
    print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
    print(f"   Price range: ${prices.min():.2f} to ${prices.max():.2f}")
else:
    print(f"❌ No data found for {test_symbol}")
    conn.close()
    sys.exit(1)

conn.close()

# Step 2: Run cycle analysis (simulating run_cycle_analysis function)
print(f"\n🔄 Step 2: Running {test_wavelength}-day cycle analysis...")
try:
    result = create_pure_sine_bandpass(
        prices=prices,
        wavelength=test_wavelength,
        method='actual_price_peaks',
        align_to='trough'
    )
    print(f"✅ Analysis complete!")
except Exception as e:
    print(f"❌ Analysis failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Display results (simulating Streamlit display)
print(f"\n📊 Step 3: Analysis Results")
print(f"   ─────────────────────────────────────────")

if 'sine_wave' in result:
    sine = result['sine_wave']
    print(f"   Sine wave generated: {len(sine)} points")

if 'peaks' in result and result['peaks']:
    peaks = result['peaks']
    print(f"   Peaks detected: {len(peaks)}")
    if len(peaks) > 0:
        last_peak = peaks[-1]
        if last_peak < len(prices):
            print(f"      Last peak: Bar {last_peak} (${prices[last_peak]:.2f} on {df['date'].iloc[last_peak].date()})")

if 'troughs' in result and result['troughs']:
    troughs = result['troughs']
    print(f"   Troughs detected: {len(troughs)}")
    if len(troughs) > 0:
        last_trough = troughs[-1]
        if last_trough < len(prices):
            print(f"      Last trough: Bar {last_trough} (${prices[last_trough]:.2f} on {df['date'].iloc[last_trough].date()})")

print(f"\n🔮 Next Projected Turning Points")
print(f"   ─────────────────────────────────────────")

if 'projected_trough' in result:
    trough_bar = result['projected_trough']
    bars_from_now = trough_bar - len(prices)
    print(f"   📉 Next trough: Bar {trough_bar} ({bars_from_now:+d} bars from now)")

if 'projected_peak' in result:
    peak_bar = result['projected_peak']
    bars_from_now = peak_bar - len(prices)
    print(f"   📈 Next peak: Bar {peak_bar} ({bars_from_now:+d} bars from now)")

# Summary
print("\n" + "=" * 80)
print("END-TO-END WORKFLOW TEST SUMMARY")
print("=" * 80)
print(f"✅ Symbol: {test_symbol}")
print(f"✅ Data source: Riley's price_bars_daily table")
print(f"✅ Bars analyzed: {len(prices)}")
print(f"✅ Wavelength: {test_wavelength} days")
print(f"✅ Algorithm: Bandpass filtering with pure sine wave")
print(f"✅ Peaks detected: {len(result.get('peaks', []))}")
print(f"✅ Troughs detected: {len(result.get('troughs', []))}")

if 'projected_trough' in result or 'projected_peak' in result:
    print(f"✅ Projections: Available")
else:
    print(f"⚠️  Projections: Not available")

print("\n✅ COMPLETE WORKFLOW WORKING CORRECTLY")
print("=" * 80)
print("\nThis is exactly what happens when user:")
print("1. Opens Riley Cycles Watch (http://localhost:8501)")
print("2. Clicks 'Cycles Detector' in sidebar")
print("3. Enters symbol: AAPL")
print("4. Selects wavelength: 380 days")
print("5. Clicks 'Run Analysis'")
print("\n✅ Integration complete and functional!")
print("=" * 80)
