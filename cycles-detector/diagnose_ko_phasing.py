#!/usr/bin/env python3
"""
Diagnose KO phasing issue
Show exactly which trough is being selected and why it's wrong
"""

import sys
import numpy as np
from scipy.signal import find_peaks
import pandas as pd

sys.path.insert(0, '/Users/bernie/Documents/Cycles Detector/Cycles Detector V14/webapp')

from data_manager import DataManager

def diagnose_ko_phasing():
    """Diagnose KO 425d phasing"""

    print("="*100)
    print("DIAGNOSING KO 425d PHASING ISSUE")
    print("="*100)

    # Load KO data
    dm = DataManager('KO')
    prices, df = dm.get_data()
    dates = df['Date'].values

    print(f"\nLoaded {len(prices)} bars")
    print(f"Date range: {dates[0]} to {dates[-1]}")
    print(f"Last date: {dates[-1]}")

    # Use 4000 bars like the UI
    if len(prices) > 4000:
        prices = prices[-4000:]
        dates = dates[-4000:]

    print(f"\nUsing last 4000 bars: {dates[0]} to {dates[-1]}")

    # Detrend
    x = np.arange(len(prices))
    coeffs = np.polyfit(x, prices, 3)
    trend = np.polyval(coeffs, x)
    detrended = prices - trend

    # Parameters for 425d cycle
    wavelength = 425
    search_window = min(len(detrended), int(wavelength * 3.0))
    recent_detrended = detrended[-search_window:]

    print(f"\nSearch window: {search_window} bars (last {search_window/252:.1f} years)")
    print(f"Search window date range: {dates[-search_window]} to {dates[-1]}")

    # Find troughs
    min_peak_distance = int(wavelength * 0.4)
    troughs_idx, trough_props = find_peaks(
        -recent_detrended,
        distance=min_peak_distance,
        prominence=np.std(recent_detrended) * 0.2
    )

    print(f"\nFound {len(troughs_idx)} troughs in search window:")
    print(f"{'Index':<10} {'Abs Index':<12} {'Date':<25} {'Prominence':<12} {'Detrended Value'}")
    print("-" * 100)

    for i, idx in enumerate(troughs_idx):
        abs_idx = len(detrended) - search_window + idx
        date = dates[abs_idx]
        prom = trough_props['prominences'][i] if 'prominences' in trough_props else 0
        value = detrended[abs_idx]
        marker = " <-- SELECTED (most recent)" if i == len(troughs_idx) - 1 else ""
        print(f"{idx:<10} {abs_idx:<12} {str(date):<25} {prom:<12.4f} {value:<12.2f}{marker}")

    # Current selection (most recent)
    if len(troughs_idx) > 0:
        selected_idx = troughs_idx[-1]
        selected_abs_idx = len(detrended) - search_window + selected_idx
        selected_date = dates[selected_abs_idx]

        print(f"\n{'='*100}")
        print("CURRENT ALGORITHM SELECTS:")
        print(f"{'='*100}")
        print(f"Index in recent_detrended: {selected_idx}")
        print(f"Absolute index: {selected_abs_idx}")
        print(f"Date: {selected_date}")
        print(f"Bars from end: {len(dates) - 1 - selected_abs_idx}")
        print(f"Days from end: ~{(len(dates) - 1 - selected_abs_idx) / 252 * 365:.0f} days")

        # Check if this is too recent
        bars_from_end = len(dates) - 1 - selected_abs_idx
        if bars_from_end < wavelength / 4:
            print(f"\n⚠️  WARNING: This trough is only {bars_from_end} bars from the end!")
            print(f"⚠️  That's {bars_from_end/wavelength*100:.1f}% of the wavelength")
            print(f"⚠️  This trough is likely still DEVELOPING and not confirmed!")

        # Find most prominent trough
        if 'prominences' in trough_props and len(trough_props['prominences']) > 0:
            most_prom_i = np.argmax(trough_props['prominences'])
            most_prom_idx = troughs_idx[most_prom_i]
            most_prom_abs_idx = len(detrended) - search_window + most_prom_idx
            most_prom_date = dates[most_prom_abs_idx]
            most_prom_value = trough_props['prominences'][most_prom_i]

            print(f"\n{'='*100}")
            print("MOST PROMINENT TROUGH (SHOULD USE THIS):")
            print(f"{'='*100}")
            print(f"Index in recent_detrended: {most_prom_idx}")
            print(f"Absolute index: {most_prom_abs_idx}")
            print(f"Date: {most_prom_date}")
            print(f"Prominence: {most_prom_value:.4f}")
            print(f"Bars from end: {len(dates) - 1 - most_prom_abs_idx}")

            if most_prom_idx != selected_idx:
                print(f"\n❌ MISMATCH: Currently using index {selected_idx} ({selected_date})")
                print(f"✅ SHOULD USE: index {most_prom_idx} ({most_prom_date}) - more prominent!")

    print(f"\n{'='*100}")
    print("RECOMMENDATION:")
    print(f"{'='*100}")
    print("1. EXCLUDE troughs within last 25% of wavelength (too recent/developing)")
    print("2. Among remaining troughs, select the MOST PROMINENT one")
    print("3. This ensures alignment to confirmed, significant troughs")

if __name__ == '__main__':
    diagnose_ko_phasing()
