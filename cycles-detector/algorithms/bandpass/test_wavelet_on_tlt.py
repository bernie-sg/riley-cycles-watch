#!/usr/bin/env python3
"""
Test wavelet bandpass algorithm on real TLT data
"""

import sys
sys.path.append('..')
sys.path.append('../..')

import numpy as np
from wavelet_bandpass import create_wavelet_bandpass_filter
from data_manager import DataManager

# Load TLT data
dm = DataManager('TLT')
prices, price_df = dm.get_data()

print(f"\n{'='*60}")
print("WAVELET BANDPASS TEST ON REAL TLT DATA")
print(f"{'='*60}\n")

print(f"Loaded {len(prices)} TLT price points")
print(f"Price range: ${np.min(prices):.2f} - ${np.max(prices):.2f}")

# Test 350d wavelength
wavelength = 350
print(f"\nTesting {wavelength}d wavelength...")

# Create wavelet bandpass
result = create_wavelet_bandpass_filter(
    prices,
    wavelength,
    bandwidth_pct=0.10,
    extend_future=700
)

print(f"\nResults:")
print(f"  Method: Weighted Morlet Wavelet")
print(f"  Phase: {result['phase_degrees']:.1f}°")
print(f"  Amplitude: {result['amplitude']:.6f}")
print(f"  Wavelength: {result['wavelength']}d")

bandpass = result['bandpass_normalized']
print(f"\nBandpass stats:")
print(f"  Total length: {len(bandpass)}")
print(f"  Historical length: {len(prices)}")
print(f"  Future projection: {len(bandpass) - len(prices)}")
print(f"  Min value: {np.min(bandpass):.6f}")
print(f"  Max value: {np.max(bandpass):.6f}")
print(f"  Mean value: {np.mean(bandpass):.6f}")
print(f"  Std dev: {np.std(bandpass):.6f}")

# Check if bandpass is varying
historical_bandpass = bandpass[:len(prices)]
if np.std(historical_bandpass) < 0.01:
    print("\n❌ WARNING: Bandpass is nearly constant! Algorithm may have a bug.")
    print(f"   First 20 values: {historical_bandpass[:20]}")
else:
    print(f"\n✓ Bandpass is varying correctly")
    print(f"   Sample values (every 500th): {historical_bandpass[::500][:10]}")

# Visualize a portion
print(f"\nRecent bandpass values (last 10):")
for i in range(-10, 0):
    print(f"  Index {len(prices)+i}: {historical_bandpass[i]:.6f}")
