#!/usr/bin/env python3
"""
Debug: Check global normalization behavior
"""
import numpy as np
import sys
sys.path.insert(0, '/Users/bernie/Documents/Cycles Detector/Cycles Detector V6/webapp')

from algorithms.heatmap.heatmap_algo import process_week_on_grid

# Load TLT data
prices = np.loadtxt('tlt_history.csv', delimiter=',', skiprows=1, usecols=1)
print(f"Loaded {len(prices)} TLT price points")

# Define wavelengths (same as webapp)
trading_wavelengths = np.arange(100, 801, 5)
calendar_wavelengths = trading_wavelengths * 1.451

# Window size
window_size = 4000

print("\n" + "="*60)
print("CHECKING GLOBAL NORMALIZATION")
print("="*60)

# Get current spectrum (week 0) - RAW
current_raw = process_week_on_grid(prices, 0, trading_wavelengths,
                                   window_size=window_size,
                                   normalize=False)

# Get some historical weeks - RAW
week_26_raw = process_week_on_grid(prices, 26, trading_wavelengths,
                                    window_size=window_size,
                                    normalize=False)

week_52_raw = process_week_on_grid(prices, 52, trading_wavelengths,
                                    window_size=window_size,
                                    normalize=False)

week_104_raw = process_week_on_grid(prices, 104, trading_wavelengths,
                                     window_size=window_size,
                                     normalize=False)

# Simulate collecting all historical data like the app does
max_weeks = (len(prices) - window_size) // 5
print(f"\nTotal weeks to process: {max_weeks}")

print("\nCollecting ALL raw spectra (this may take a moment)...")
all_spectra_raw = []
for week in range(max_weeks):
    spectrum = process_week_on_grid(prices, week, trading_wavelengths,
                                    window_size=window_size,
                                    normalize=False)
    all_spectra_raw.append(spectrum)

all_spectra_raw = np.array(all_spectra_raw)
global_max = np.max(all_spectra_raw)

print(f"\n{'='*60}")
print(f"GLOBAL MAXIMUM across all {max_weeks} weeks: {global_max:.6f}")
print(f"{'='*60}")

# Find where the global max occurs
max_week_idx = np.unravel_index(np.argmax(all_spectra_raw), all_spectra_raw.shape)[0]
max_wl_idx = np.unravel_index(np.argmax(all_spectra_raw), all_spectra_raw.shape)[1]
max_wavelength = calendar_wavelengths[max_wl_idx]
max_week_ago = max_weeks - 1 - max_week_idx

print(f"\nGlobal max occurs at:")
print(f"  Week: {max_week_ago} weeks ago")
print(f"  Wavelength: {max_wavelength:.0f}d")

# Check 625d values
idx_625 = np.argmin(np.abs(calendar_wavelengths - 625))
actual_wl_625 = calendar_wavelengths[idx_625]

print(f"\n{'='*60}")
print(f"625d CYCLE ANALYSIS (actual: {actual_wl_625:.0f}d)")
print(f"{'='*60}")

print(f"\nRAW values (before normalization):")
print(f"  Current (week 0):     {current_raw[idx_625]:.6f}")
print(f"  6 months ago (w26):   {week_26_raw[idx_625]:.6f}")
print(f"  1 year ago (w52):     {week_52_raw[idx_625]:.6f}")
print(f"  2 years ago (w104):   {week_104_raw[idx_625]:.6f}")

print(f"\nAfter GLOBAL normalization (÷ {global_max:.6f}):")
print(f"  Current (week 0):     {current_raw[idx_625]/global_max:.6f}")
print(f"  6 months ago (w26):   {week_26_raw[idx_625]/global_max:.6f}")
print(f"  1 year ago (w52):     {week_52_raw[idx_625]/global_max:.6f}")
print(f"  2 years ago (w104):   {week_104_raw[idx_625]/global_max:.6f}")

# Find top peaks in CURRENT spectrum after global norm
current_norm = current_raw / global_max
top_indices = np.argsort(current_norm)[-5:][::-1]

print(f"\n{'='*60}")
print(f"TOP 5 PEAKS in CURRENT spectrum (after global norm)")
print(f"{'='*60}")
for i, idx in enumerate(top_indices, 1):
    wl = calendar_wavelengths[idx]
    power_raw = current_raw[idx]
    power_norm = current_norm[idx]
    marker = " ← 625d region" if abs(wl - 625) < 20 else ""
    print(f"  {i}. {wl:.0f}d: raw={power_raw:.6f}, norm={power_norm:.6f}{marker}")

# Check if 625d even meets the 0.25 threshold
print(f"\n{'='*60}")
print(f"PEAK FILTERING CHECK (threshold = 0.25)")
print(f"{'='*60}")
print(f"625d normalized power: {current_norm[idx_625]:.6f}")
if current_norm[idx_625] >= 0.25:
    print(f"✓ 625d PASSES the 0.25 threshold - should appear in heatmap")
else:
    print(f"✗ 625d FAILS the 0.25 threshold - will be filtered out")
    print(f"  Needs to be: {0.25:.6f}")
    print(f"  Currently:   {current_norm[idx_625]:.6f}")
    print(f"  Shortfall:   {0.25 - current_norm[idx_625]:.6f}")
