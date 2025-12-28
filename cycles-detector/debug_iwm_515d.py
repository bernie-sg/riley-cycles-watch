#!/usr/bin/env python3
"""
Debug IWM 515d alignment to understand why labels go back to 2001
"""
import sys
import numpy as np

sys.path.insert(0, '/Users/bernie/Documents/Cycles Detector/Cycles Detector V14/webapp')

from data_manager import DataManager
from algorithms.bandpass.pure_sine_bandpass import create_pure_sine_bandpass

# Load IWM data
dm = DataManager('IWM')
prices, df = dm.get_data()
dates = df['Date'].values

# Use 4000 bars like the UI
if len(prices) > 4000:
    prices = prices[-4000:]
    dates = dates[-4000:]

print("="*100)
print("DEBUGGING IWM 515d TROUGH ALIGNMENT")
print("="*100)
print(f"\nLoaded {len(prices)} bars")
print(f"Date range: {dates[0]} to {dates[-1]}")
print(f"Last date: {dates[-1]}")

# Call the bandpass function with trough alignment
print(f"\nCalling create_pure_sine_bandpass()...")
print(f"  wavelength=515, align_to='trough', method='actual_price_peaks'")

try:
    result = create_pure_sine_bandpass(
        prices=prices,
        wavelength=515,
        bandwidth_pct=0.10,
        extend_future=700,
        method='actual_price_peaks',
        align_to='trough'
    )

    print(f"\n✅ Function completed successfully")

    # Check what we got
    peaks = result.get('peaks', [])
    troughs = result.get('troughs', [])

    print(f"\n{'='*100}")
    print("RESULT ANALYSIS")
    print(f"{'='*100}")
    print(f"Total peaks: {len(peaks)}")
    print(f"Total troughs: {len(troughs)}")

    if len(troughs) > 0:
        print(f"\n{'='*60}")
        print("TROUGH LABELS")
        print(f"{'='*60}")
        print(f"{'Index':<10} {'Date':<20} {'Bars from End'}")
        print("-"*60)

        for i, idx in enumerate(troughs[:10]):  # First 10
            date = dates[idx] if idx < len(dates) else 'N/A'
            bars_from_end = len(dates) - 1 - idx
            print(f"{idx:<10} {str(date):<20} {bars_from_end}")

        if len(troughs) > 10:
            print(f"... ({len(troughs) - 10} more troughs)")

        # Show last 3 troughs
        print(f"\nLast 3 troughs:")
        for i, idx in enumerate(troughs[-3:]):
            date = dates[idx] if idx < len(dates) else 'N/A'
            bars_from_end = len(dates) - 1 - idx
            print(f"  {idx:<10} {str(date):<20} {bars_from_end}")

    if len(peaks) > 0:
        print(f"\n{'='*60}")
        print("PEAK LABELS")
        print(f"{'='*60}")
        print(f"First 5 peaks:")
        for i, idx in enumerate(peaks[:5]):
            date = dates[idx] if idx < len(dates) else 'N/A'
            bars_from_end = len(dates) - 1 - idx
            print(f"  {idx:<10} {str(date):<20} {bars_from_end}")

        print(f"\nLast 3 peaks:")
        for i, idx in enumerate(peaks[-3:]):
            date = dates[idx] if idx < len(dates) else 'N/A'
            bars_from_end = len(dates) - 1 - idx
            print(f"  {idx:<10} {str(date):<20} {bars_from_end}")

    # Check phase information
    print(f"\n{'='*100}")
    print("PHASE INFORMATION")
    print(f"{'='*100}")
    print(f"Phase degrees: {result.get('phase_degrees', 'N/A')}")
    print(f"Method: {result.get('method', 'N/A')}")
    print(f"Amplitude: {result.get('amplitude', 'N/A')}")
    print(f"Wavelength: {result.get('wavelength', 'N/A')}")

    # Analyze why labels go back so far
    print(f"\n{'='*100}")
    print("ANALYSIS: Why do labels go back to 2001?")
    print(f"{'='*100}")

    if len(troughs) > 0:
        first_trough_idx = troughs[0]
        first_trough_date = dates[first_trough_idx] if first_trough_idx < len(dates) else 'N/A'

        print(f"First trough label: index={first_trough_idx}, date={first_trough_date}")
        print(f"\nThe sine wave is phase-aligned to a recent confirmed trough,")
        print(f"but then the algorithm generates labels for ALL extrema by")
        print(f"propagating the sine wave backward and forward in time.")
        print(f"\nThis means labels will extend through the entire data history.")
        print(f"\nFor trading purposes (recency focus), we may want to:")
        print(f"  1. Only show labels within the last N years (e.g., 3-5 years)")
        print(f"  2. Or highlight recent labels differently in the UI")
        print(f"  3. Or filter labels when sending to frontend based on date range")

except Exception as e:
    print(f"\n❌ Exception occurred:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
