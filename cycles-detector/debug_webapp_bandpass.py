#!/usr/bin/env python3
"""
Debug what the webapp is actually generating vs standalone test
"""
import numpy as np
from data_manager import DataManager
from algorithms.bandpass.pure_sine_bandpass import create_pure_sine_bandpass

# Load TLT - EXACTLY as webapp does
dm = DataManager('TLT')
prices, dates = dm.get_data()

# Use last 4000 bars as webapp does
window_size = 4000
prices = prices[-window_size:]

print(f"\n{'='*60}")
print(f"DEBUGGING WEBAPP BANDPASS")
print(f"{'='*60}\n")
print(f"Using {len(prices)} price bars (last {window_size})")

for wavelength in [350, 470, 625]:
    print(f"\n{'-'*60}")
    print(f"Wavelength: {wavelength}d")
    print(f"{'-'*60}")

    result = create_pure_sine_bandpass(
        prices,
        wavelength,
        bandwidth_pct=0.10,
        extend_future=700
    )

    bp = result['bandpass_normalized']
    historical_bp = bp[:len(prices)]

    print(f"Phase: {result['phase_degrees']:.1f}°")
    print(f"Amplitude: {result['amplitude']:.6f}")
    print(f"Total bandpass length: {len(bp)}")
    print(f"Historical bandpass length: {len(historical_bp)}")
    print(f"Historical min: {np.min(historical_bp):.6f}")
    print(f"Historical max: {np.max(historical_bp):.6f}")
    print(f"Historical std: {np.std(historical_bp):.6f}")

    # Check if it's a pure sine wave
    if len(bp) >= wavelength * 3:
        # Compare 3 consecutive cycles
        cycle1 = bp[0:wavelength]
        cycle2 = bp[wavelength:2*wavelength]
        cycle3 = bp[2*wavelength:3*wavelength]

        corr12 = np.corrcoef(cycle1, cycle2)[0, 1]
        corr23 = np.corrcoef(cycle2, cycle3)[0, 1]

        print(f"Cycle 1-2 correlation: {corr12:.6f}")
        print(f"Cycle 2-3 correlation: {corr23:.6f}")

        if corr12 > 0.99 and corr23 > 0.99:
            print("✓ SMOOTH SINE WAVE")
        else:
            print("✗ IRREGULAR WAVE!")

    # Print first and last 5 values
    print(f"First 5 values: {historical_bp[:5]}")
    print(f"Last 5 values: {historical_bp[-5:]}")

print(f"\n{'='*60}")
print("If any wavelength shows 'IRREGULAR WAVE!' then that's the problem")
print(f"{'='*60}\n")
