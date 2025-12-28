#!/usr/bin/env python3
"""
Debug: Why is 625d not showing up in heatmap?
"""
import numpy as np
import sys
sys.path.insert(0, '/Users/bernie/Documents/Cycles Detector/Cycles Detector V6/webapp')

from algorithms.heatmap.heatmap_algo import process_week_on_grid
from data_manager import DataManager

# Load TLT data
dm = DataManager('TLT')
prices, df = dm.get_data()

print(f"Loaded {len(prices)} TLT price points")

# Define wavelengths (EXACT same as webapp - CALENDAR DAYS with step=1)
wavelengths = np.arange(100, 801, 1)  # Calendar days, NOT trading days!

# Window size
window_size = 4000

print("\n" + "="*60)
print("CHECKING 625d VISIBILITY IN HEATMAP")
print("="*60)

# Find 625d index
idx_625 = 625 - 100  # Direct index since we're using 1-day steps starting at 100
actual_wl_625 = wavelengths[idx_625]
print(f"\n625d index: {idx_625}, actual wavelength: {actual_wl_625:.0f}d")

# Collect ALL raw spectra (same as app.py does)
max_weeks = (len(prices) - window_size) // 5
print(f"Total weeks to process: {max_weeks}")

print("\nCollecting ALL raw spectra (this may take a moment)...")
heatmap_raw = []

for week in range(max_weeks):
    spectrum = process_week_on_grid(prices, week, wavelengths,
                                   window_size=window_size,
                                   suppress_long_cycles=True,
                                   normalize=False)
    heatmap_raw.append(spectrum)

    if week % 50 == 0:
        print(f"  Processed {week}/{max_weeks} weeks")

heatmap_raw = np.array(heatmap_raw)

# Global normalization (EXACTLY as app.py does it)
global_max = np.max(heatmap_raw)
print(f"\nGlobal maximum: {global_max:.6f}")

heatmap_normalized = heatmap_raw / global_max
power_spectrum_normalized = heatmap_raw[0] / global_max  # Week 0 is most recent

print(f"\n{'='*60}")
print(f"625d ANALYSIS")
print(f"{'='*60}")

# Check raw values over recent weeks
print(f"\nRAW values at 625d over recent weeks:")
for week in range(min(10, max_weeks)):
    raw_val = heatmap_raw[week, idx_625]
    norm_val = heatmap_normalized[week, idx_625]
    print(f"  Week {week:2d}: raw={raw_val:.6f}, normalized={norm_val:.4f}")

# Check current power spectrum
print(f"\nCurrent (week 0) power spectrum at 625d:")
print(f"  Raw: {heatmap_raw[0, idx_625]:.6f}")
print(f"  Normalized: {power_spectrum_normalized[idx_625]:.4f}")

# Find top peaks in CURRENT spectrum
top_indices = np.argsort(power_spectrum_normalized)[-10:][::-1]

print(f"\n{'='*60}")
print(f"TOP 10 PEAKS in CURRENT spectrum (normalized)")
print(f"{'='*60}")
for i, idx in enumerate(top_indices, 1):
    wl = calendar_wavelengths[idx]
    power_raw = heatmap_raw[0, idx]
    power_norm = power_spectrum_normalized[idx]
    marker = " ← 625d region" if abs(wl - 625) < 20 else ""
    print(f"  {i:2d}. {wl:4.0f}d: raw={power_raw:.6f}, norm={power_norm:.4f}{marker}")

# Check where global max occurs
max_week_idx, max_wl_idx = np.unravel_index(np.argmax(heatmap_raw), heatmap_raw.shape)
max_wavelength = calendar_wavelengths[max_wl_idx]
max_value = heatmap_raw[max_week_idx, max_wl_idx]

print(f"\n{'='*60}")
print(f"GLOBAL MAXIMUM LOCATION")
print(f"{'='*60}")
print(f"  Week: {max_week_idx} (weeks ago from most recent)")
print(f"  Wavelength: {max_wavelength:.0f}d")
print(f"  Raw value: {max_value:.6f}")

# Check if 625d is ever strong in history
print(f"\n{'='*60}")
print(f"625d THROUGH TIME (find when it was strongest)")
print(f"{'='*60}")

# Find top 5 weeks where 625d was strongest
strongest_625d_weeks = np.argsort(heatmap_raw[:, idx_625])[-5:][::-1]
for i, week in enumerate(strongest_625d_weeks, 1):
    raw_val = heatmap_raw[week, idx_625]
    norm_val = heatmap_normalized[week, idx_625]
    print(f"  {i}. Week {week:3d}: raw={raw_val:.6f}, normalized={norm_val:.4f}")

# Compare 625d to other visible cycles
print(f"\n{'='*60}")
print(f"COMPARISON: 625d vs OTHER PEAKS (current week 0)")
print(f"{'='*60}")

cycles_to_check = [350, 470, 625, 825]
for cycle in cycles_to_check:
    idx = np.argmin(np.abs(calendar_wavelengths - cycle))
    actual_wl = calendar_wavelengths[idx]
    raw_val = heatmap_raw[0, idx]
    norm_val = power_spectrum_normalized[idx]
    print(f"  {actual_wl:4.0f}d: raw={raw_val:.6f}, normalized={norm_val:.4f}")
