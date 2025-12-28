#!/usr/bin/env python3
"""
Verify what data is actually being sent to frontend
"""
import numpy as np
import requests
import json

# Get data from API
response = requests.get('http://localhost:5001/api/analyze?symbol=TLT')
data = response.json()

# Extract heatmap and power spectrum
heatmap = np.array(data['heatmap']['data'])
wavelengths = np.array(data['heatmap']['wavelengths'])
power_spectrum = np.array(data['power_spectrum']['amplitudes'])

print("="*70)
print("HEATMAP DATA STRUCTURE VERIFICATION")
print("="*70)

print(f"\nHeatmap shape: {heatmap.shape}")
print(f"Wavelengths length: {len(wavelengths)}")
print(f"Power spectrum length: {len(power_spectrum)}")

# Find 625d
idx_625 = np.argmin(np.abs(wavelengths - 625))
actual_wl = wavelengths[idx_625]

print(f"\n625d Analysis (actual wavelength: {actual_wl}d, index: {idx_625})")
print("="*70)

# Check power spectrum value
print(f"\nPower spectrum at 625d: {power_spectrum[idx_625]:.4f}")

# Check heatmap structure
print(f"\nHeatmap data organization:")
print(f"  Number of time slices: {heatmap.shape[0]}")
print(f"  Number of wavelengths per slice: {heatmap.shape[1]}")

# Get most recent time slice (should match power spectrum)
most_recent_idx = heatmap.shape[0] - 1  # Last time slice
most_recent_slice = heatmap[most_recent_idx]

print(f"\nMost recent heatmap slice (time index {most_recent_idx}):")
print(f"  Value at 625d (wavelength index {idx_625}): {most_recent_slice[idx_625]:.4f}")

# Compare to power spectrum
print(f"\nCOMPARISON:")
print(f"  Power spectrum at 625d: {power_spectrum[idx_625]:.4f}")
print(f"  Heatmap (most recent) at 625d: {most_recent_slice[idx_625]:.4f}")
print(f"  Match? {np.isclose(power_spectrum[idx_625], most_recent_slice[idx_625])}")

# Check if they're TRANSPOSED
first_time_slice = heatmap[0]
print(f"\nFirst time slice value at 625d: {first_time_slice[idx_625]:.4f}")

# Try the OTHER way - what if heatmap[wavelength_idx][time_idx]?
print(f"\n\nTrying TRANSPOSED interpretation:")
print(f"  heatmap[{idx_625}][{most_recent_idx}] = {heatmap[idx_625][most_recent_idx]:.4f}")
print(f"  heatmap[{idx_625}][0] = {heatmap[idx_625][0]:.4f}")

# Check all time slices for 625d
print(f"\n\n625d values across ALL time slices:")
print(f"  Shape interpretation: heatmap[time][wavelength]")
for i in [0, 1, 2, -3, -2, -1]:
    val = heatmap[i][idx_625]
    print(f"    Time index {i:4d}: {val:.4f}")

print(f"\n\nAlternate interpretation: heatmap[wavelength][time]")
if len(heatmap) > idx_625:
    for i in [0, 1, 2, -3, -2, -1]:
        val = heatmap[idx_625][i]
        print(f"    Time index {i:4d}: {val:.4f}")

# Find which interpretation matches power spectrum
print(f"\n\n{'='*70}")
print("FINDING CORRECT ORIENTATION")
print("="*70)

# Test a few wavelengths
test_wavelengths = [350, 470, 625]
for wl in test_wavelengths:
    idx = np.argmin(np.abs(wavelengths - wl))
    ps_val = power_spectrum[idx]

    # Try both orientations
    val_time_wl = heatmap[-1][idx]  # heatmap[time][wavelength]
    val_wl_time = heatmap[idx][-1] if len(heatmap) > idx else None

    print(f"\n{wl}d (index {idx}):")
    print(f"  Power spectrum: {ps_val:.4f}")
    print(f"  heatmap[time=-1][wl={idx}]: {val_time_wl:.4f} {'✓ MATCH' if np.isclose(ps_val, val_time_wl) else '✗ NO MATCH'}")
    if val_wl_time is not None:
        print(f"  heatmap[wl={idx}][time=-1]: {val_wl_time:.4f} {'✓ MATCH' if np.isclose(ps_val, val_wl_time) else '✗ NO MATCH'}")
