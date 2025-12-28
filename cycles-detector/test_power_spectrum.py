#!/usr/bin/env python3
"""
Test power spectrum with and without log transform
To see which matches SIGMA-L's 526-day TLT cycle detection
"""

import numpy as np
import sys
sys.path.append('algorithms/heatmap')
from heatmap_algo import create_high_q_morlet, compute_power
from scipy.signal import find_peaks

# Load TLT data
prices = np.loadtxt('tlt_prices.txt')
print(f"Loaded {len(prices)} TLT prices")
print(f"Using window size: 5689 bars (SIGMA-L standard)")

window_size = 5689
wavelengths = np.arange(100, 801, 5)

# Get last 5689 bars
data = prices[-window_size:]

print("\n" + "="*60)
print("TEST 1: With Log Transform (current implementation)")
print("="*60)

# Log transform + linear detrend
data_log = np.log(data)
x = np.arange(len(data_log))
coeffs = np.polyfit(x, data_log, 1)
trend = np.polyval(coeffs, x)
data_log_detrended = data_log - trend

# Compute spectrum
spectrum_log = np.array([compute_power(data_log_detrended, wl) for wl in wavelengths])

# Normalize
spectrum_log = spectrum_log / np.max(spectrum_log)

# Find peaks
peaks_log, props_log = find_peaks(spectrum_log, height=0.15, distance=8)
sorted_peaks_log = peaks_log[np.argsort(spectrum_log[peaks_log])[::-1]]

print("\nTop 5 detected cycles (WITH log):")
for i, peak_idx in enumerate(sorted_peaks_log[:5]):
    wl = wavelengths[peak_idx]
    power = spectrum_log[peak_idx]
    cal_days = wl * 1.451  # Trading to calendar days
    print(f"  {i+1}. {cal_days:.0f} calendar days ({wl:.0f} trading days) - Power: {power:.3f}")


print("\n" + "="*60)
print("TEST 2: Without Log Transform (raw close prices)")
print("="*60)

# Raw prices + linear detrend
x = np.arange(len(data))
coeffs = np.polyfit(x, data, 1)
trend = np.polyval(coeffs, x)
data_raw_detrended = data - trend

# Compute spectrum
spectrum_raw = np.array([compute_power(data_raw_detrended, wl) for wl in wavelengths])

# Normalize
spectrum_raw = spectrum_raw / np.max(spectrum_raw)

# Find peaks
peaks_raw, props_raw = find_peaks(spectrum_raw, height=0.15, distance=8)
sorted_peaks_raw = peaks_raw[np.argsort(spectrum_raw[peaks_raw])[::-1]]

print("\nTop 5 detected cycles (WITHOUT log):")
for i, peak_idx in enumerate(sorted_peaks_raw[:5]):
    wl = wavelengths[peak_idx]
    power = spectrum_raw[peak_idx]
    cal_days = wl * 1.451
    print(f"  {i+1}. {cal_days:.0f} calendar days ({wl:.0f} trading days) - Power: {power:.3f}")


print("\n" + "="*60)
print("SIGMA-L REFERENCE: 526 calendar days (363 trading days)")
print("="*60)

# Check which is closer to 526 calendar days (363 trading days)
target_cal_days = 526
target_trading_days = 363

if len(sorted_peaks_log) > 0:
    top_log_wl = wavelengths[sorted_peaks_log[0]]
    top_log_cal = top_log_wl * 1.451
    diff_log = abs(top_log_cal - target_cal_days)
    print(f"\nWith LOG:    Top = {top_log_cal:.0f} cal days, Diff = {diff_log:.0f} days")

if len(sorted_peaks_raw) > 0:
    top_raw_wl = wavelengths[sorted_peaks_raw[0]]
    top_raw_cal = top_raw_wl * 1.451
    diff_raw = abs(top_raw_cal - target_cal_days)
    print(f"Without LOG: Top = {top_raw_cal:.0f} cal days, Diff = {diff_raw:.0f} days")

if len(sorted_peaks_log) > 0 and len(sorted_peaks_raw) > 0:
    if diff_raw < diff_log:
        print("\n✓ WITHOUT log transform is closer to SIGMA-L!")
    else:
        print("\n✓ WITH log transform is closer to SIGMA-L!")