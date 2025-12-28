#!/usr/bin/env python3
"""
Debug: Exact replication of app.py analysis to verify 625d
"""
import numpy as np
from scipy.signal import find_peaks
import sys
sys.path.insert(0, '/Users/bernie/Documents/Cycles Detector/Cycles Detector V6/webapp')

from algorithms.heatmap.heatmap_algo import process_week_on_grid
from data_manager import DataManager

# Load TLT data
dm = DataManager('TLT')
prices, df = dm.get_data()

print(f"Loaded {len(prices)} TLT price points\n")

# EXACT same parameters as app.py
wavelengths = np.arange(100, 801, 1)  # Calendar days
window_size = 4000
suppress_long_cycles = True

print("="*70)
print("EXACT REPLICATION OF APP.PY ANALYSIS")
print("="*70)

# 1. Get power spectrum (week 0 = most recent)
power_spectrum_raw = process_week_on_grid(prices, 0, wavelengths,
                                         window_size=window_size,
                                         suppress_long_cycles=suppress_long_cycles,
                                         normalize=False)

# 2. Collect ALL raw heatmap spectra
max_weeks = (len(prices) - window_size) // 5
print(f"\nProcessing {max_weeks} weeks of heatmap data...")

heatmap_raw = []
for week in range(max_weeks):
    spectrum = process_week_on_grid(prices, week, wavelengths,
                                   window_size=window_size,
                                   suppress_long_cycles=suppress_long_cycles,
                                   normalize=False)
    heatmap_raw.append(spectrum)

    if week % 50 == 0:
        print(f"  Processed {week}/{max_weeks}")

heatmap_raw = np.array(heatmap_raw)

# 3. Global normalization
global_max = np.max(heatmap_raw)
print(f"\nGlobal maximum: {global_max:.6f}")

heatmap_normalized = heatmap_raw / global_max
power_spectrum = power_spectrum_raw / global_max

# 4. Find peaks
peaks, _ = find_peaks(power_spectrum, height=0.25, distance=8)
sorted_peaks = peaks[np.argsort(power_spectrum[peaks])[::-1]]

print(f"\n{'='*70}")
print(f"PEAK DETECTION RESULTS (threshold=0.25, distance=8)")
print(f"{'='*70}")

for i, peak_idx in enumerate(sorted_peaks[:10], 1):
    wl = wavelengths[peak_idx]
    amplitude = power_spectrum[peak_idx]
    print(f"  {i:2d}. {wl:4.0f}d: amplitude={amplitude:.4f}")

# 5. Specific 625d analysis
idx_625 = 625 - 100  # Direct index
print(f"\n{'='*70}")
print(f"625d DETAILED ANALYSIS (index={idx_625})")
print(f"{'='*70}")

print(f"\nCurrent (week 0):")
print(f"  Raw: {power_spectrum_raw[idx_625]:.6f}")
print(f"  Normalized: {power_spectrum[idx_625]:.4f}")
print(f"  Is peak? {idx_625 in peaks}")

# Check if 625d meets peak criteria manually
if power_spectrum[idx_625] >= 0.25:
    # Check if it's a local maximum (distance=8)
    nearby_indices = range(max(0, idx_625-8), min(len(power_spectrum), idx_625+9))
    is_local_max = all(power_spectrum[idx_625] >= power_spectrum[j] for j in nearby_indices if j != idx_625)
    print(f"  Meets height threshold (≥0.25)? YES")
    print(f"  Is local maximum (distance=8)? {is_local_max}")
else:
    print(f"  Meets height threshold (≥0.25)? NO (need {0.25:.4f}, have {power_spectrum[idx_625]:.4f})")

# 6. Compare to visible cycles
print(f"\n{'='*70}")
print(f"COMPARISON TO OTHER CYCLES")
print(f"{'='*70}")

test_cycles = [350, 470, 625, 825]
for cycle in test_cycles:
    idx = cycle - 100
    raw = power_spectrum_raw[idx]
    norm = power_spectrum[idx]
    is_peak = idx in peaks
    print(f"  {cycle}d: raw={raw:.6f}, norm={norm:.4f}, is_peak={is_peak}")

# 7. Heatmap values at 625d over time
print(f"\n{'='*70}")
print(f"625d THROUGH TIME (heatmap column)")
print(f"{'='*70}")

print(f"\nRecent weeks:")
for week in range(min(10, max_weeks)):
    raw_val = heatmap_raw[week, idx_625]
    norm_val = heatmap_normalized[week, idx_625]
    print(f"  Week {week:2d}: raw={raw_val:.6f}, normalized={norm_val:.4f}")

# Find when 625d was strongest
strongest_weeks = np.argsort(heatmap_raw[:, idx_625])[-5:][::-1]
print(f"\nStrongest 625d weeks in history:")
for i, week in enumerate(strongest_weeks, 1):
    raw_val = heatmap_raw[week, idx_625]
    norm_val = heatmap_normalized[week, idx_625]
    print(f"  {i}. Week {week:3d}: raw={raw_val:.6f}, normalized={norm_val:.4f}")

# 8. Where does global max occur?
max_week, max_wl_idx = np.unravel_index(np.argmax(heatmap_raw), heatmap_raw.shape)
max_wl = wavelengths[max_wl_idx]

print(f"\n{'='*70}")
print(f"GLOBAL MAXIMUM LOCATION")
print(f"{'='*70}")
print(f"  Week: {max_week}")
print(f"  Wavelength: {max_wl:.0f}d")
print(f"  Value: {global_max:.6f}")
