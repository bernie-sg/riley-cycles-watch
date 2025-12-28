#!/usr/bin/env python3
"""
Test analysis with 2000 bars window
"""

import numpy as np
import sys
sys.path.append('algorithms/heatmap')
from heatmap_algo import process_week_on_grid
from scipy.signal import find_peaks
from data_manager import DataManager

# Load data
dm = DataManager('TLT')
prices, df = dm.get_data()

print("=" * 60)
print("ANALYSIS WITH 2000 BARS WINDOW")
print("=" * 60)
print(f"Total data: {len(prices)} bars ({len(prices)/252:.1f} years)")
print()

# Parameters
window_size = 2000
wavelengths = np.arange(100, 801, 5)  # Step=5 for speed

print(f"Window size: {window_size} bars")
print(f"Wavelength range: {wavelengths[0]}-{wavelengths[-1]} trading days")
print()

# 1. POWER SPECTRUM
print("Computing power spectrum...")
power_spectrum = process_week_on_grid(prices, 0, wavelengths,
                                     window_size=window_size,
                                     suppress_long_cycles=True)

# Find peaks
peaks, properties = find_peaks(power_spectrum, height=0.15, distance=8)
sorted_peaks = peaks[np.argsort(power_spectrum[peaks])[::-1]]

print(f"\nDETECTED PEAKS (top 10):")
print("-" * 60)
for i, peak_idx in enumerate(sorted_peaks[:10], 1):
    wavelength = wavelengths[peak_idx]
    amplitude = power_spectrum[peak_idx]
    years = wavelength / 252
    print(f"{i:2d}. {wavelength:3.0f} trading days ({years:.2f} years) - Power: {amplitude:.3f}")

# 2. HEATMAP
max_weeks = (len(prices) - window_size) // 5
years_history = max_weeks / 52

print(f"\nHEATMAP COVERAGE:")
print("-" * 60)
print(f"Available weeks: {max_weeks} ({years_history:.1f} years of history)")
print(f"From: {df['Date'].iloc[window_size]} to {df['Date'].iloc[-1]}")
