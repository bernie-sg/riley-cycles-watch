#!/usr/bin/env python3
"""
Test what's actually happening with different wavelengths
"""
import sys
import numpy as np
from algorithms.bandpass.pure_sine_bandpass import create_pure_sine_bandpass
from data_manager import DataManager

# Load TLT
dm = DataManager('TLT')
prices, _ = dm.get_data()

print(f"Loaded {len(prices)} TLT prices\n")

wavelengths = [350, 470, 625]

for wl in wavelengths:
    result = create_pure_sine_bandpass(prices, wl, 0.10, 700)

    bp = result['bandpass_normalized']

    print(f"{'='*60}")
    print(f"Wavelength: {wl}d")
    print(f"{'='*60}")
    print(f"Phase: {result['phase_degrees']:.1f}°")
    print(f"Amplitude: {result['amplitude']:.6f}")
    print(f"Bandpass length: {len(bp)}")
    print(f"Bandpass min: {np.min(bp):.6f}")
    print(f"Bandpass max: {np.max(bp):.6f}")
    print(f"Bandpass std: {np.std(bp):.6f}")

    # Check if it's actually a pure sine by checking periodicity
    # A pure sine wave should have values that repeat every wavelength
    if len(bp) > wl * 2:
        cycle1 = bp[:wl]
        cycle2 = bp[wl:2*wl]
        correlation = np.corrcoef(cycle1, cycle2)[0, 1]
        print(f"Cycle-to-cycle correlation: {correlation:.6f} (should be ~1.0 for pure sine)")

    # Check the last 10 values
    print(f"Last 10 values: {bp[-10:]}")
    print()
