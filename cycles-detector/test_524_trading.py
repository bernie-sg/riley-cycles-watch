#!/usr/bin/env python3
"""Test if SIGMA-L uses wavelength = data index (trading days) directly"""

import numpy as np
import sys
sys.path.append('algorithms/heatmap')
from heatmap_algo import process_week_on_grid

prices = np.loadtxt('tlt_prices.txt')
print(f"Total points: {len(prices)} (trading days)\n")

# Test around 524 TRADING days (not calendar converted)
wavelengths = np.arange(500, 551, 1)  # Fine scan around 524

print("=== Scanning 500-550 trading day wavelengths ===")
spectrum = process_week_on_grid(prices, 0, wavelengths, window_size=len(prices))

# Find peak
peak_idx = np.argmax(spectrum)
print(f"Peak at: {wavelengths[peak_idx]} trading days, power: {spectrum[peak_idx]:.3f}")

# Check exact 524
idx_524 = np.where(wavelengths == 524)[0][0]
print(f"At 524: power = {spectrum[idx_524]:.3f}")

print(f"\nTop 10 in this range:")
sorted_indices = np.argsort(spectrum)[::-1]
for i in range(min(10, len(sorted_indices))):
    idx = sorted_indices[i]
    print(f"  {wavelengths[idx]:3.0f} trading days: {spectrum[idx]:.3f}")