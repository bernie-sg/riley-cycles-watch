#!/usr/bin/env python3
"""Test with FULL data sample like SIGMA-L (5688 vs 4000)"""

import numpy as np
import sys
sys.path.append('algorithms/heatmap')
from heatmap_algo import process_week_on_grid

# Load data
prices = np.loadtxt('tlt_prices.txt')
print(f"Total data points: {len(prices)}")

# Test wavelengths around 524 days
wavelengths = np.arange(100, 801, 5)

print("\n=== TEST 1: 4000 window (current V4) ===")
spectrum_4000 = process_week_on_grid(prices, 0, wavelengths, window_size=4000)
peak_idx = np.argmax(spectrum_4000)
print(f"Strongest cycle: {wavelengths[peak_idx]} days, power: {spectrum_4000[peak_idx]:.3f}")

# Find 524d area
target_idx = np.argmin(np.abs(wavelengths - 524))
print(f"524d cycle power: {spectrum_4000[target_idx]:.3f}")

print("\n=== TEST 2: 5828 window (FULL data like SIGMA-L) ===")
spectrum_full = process_week_on_grid(prices, 0, wavelengths, window_size=5828)
peak_idx = np.argmax(spectrum_full)
print(f"Strongest cycle: {wavelengths[peak_idx]} days, power: {spectrum_full[peak_idx]:.3f}")

# Find 524d area
print(f"524d cycle power: {spectrum_full[target_idx]:.3f}")

print("\n=== DIFFERENCE ===")
print(f"524d power change: {spectrum_full[target_idx]:.3f} - {spectrum_4000[target_idx]:.3f} = {spectrum_full[target_idx] - spectrum_4000[target_idx]:+.3f}")
print(f"\nTop 5 cycles (FULL data):")
sorted_indices = np.argsort(spectrum_full)[::-1]
for i in range(5):
    idx = sorted_indices[i]
    print(f"  {wavelengths[idx]:3.0f} days: {spectrum_full[idx]:.3f}")