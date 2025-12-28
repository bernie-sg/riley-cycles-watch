#!/usr/bin/env python3
"""
Test the new bandpass implementation for all three wavelengths
"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from data_manager import DataManager
from algorithms.bandpass.pure_sine_bandpass import create_pure_sine_bandpass

# Load TLT data
dm = DataManager('TLT')
prices, _ = dm.get_data()

print(f"Loaded {len(prices)} TLT prices")

wavelengths = [350, 470, 625]

fig, axes = plt.subplots(len(wavelengths), 1, figsize=(16, 12))
fig.patch.set_facecolor('black')

for idx, wavelength in enumerate(wavelengths):
    print(f"\n{'='*60}")
    print(f"Testing wavelength: {wavelength}d")

    try:
        result = create_pure_sine_bandpass(
            prices,
            wavelength,
            bandwidth_pct=0.10,
            extend_future=700
        )

        print(f"✓ Success!")
        print(f"  Phase: {result['phase_degrees']:.1f}°")
        print(f"  Amplitude: {result['amplitude']:.6f}")
        print(f"  Method: {result['method']}")
        print(f"  Bandpass length: {len(result['bandpass_normalized'])}")

        # Check if sine wave is smooth
        bp = result['bandpass_normalized']
        historical_bp = bp[:len(prices)]

        # Check min/max
        print(f"  Bandpass min: {np.min(historical_bp):.6f}")
        print(f"  Bandpass max: {np.max(historical_bp):.6f}")
        print(f"  Bandpass std: {np.std(historical_bp):.6f}")

        # Plot
        ax = axes[idx]
        ax.set_facecolor('black')

        # Show last 1500 bars
        recent_prices = prices[-1500:]
        recent_bandpass = historical_bp[-1500:]

        # Scale bandpass to price range
        price_mean = np.mean(recent_prices)
        price_range = np.max(recent_prices) - np.min(recent_prices)
        scaled_bp = recent_bandpass * (price_range * 0.15) + price_mean

        ax.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Price')
        ax.plot(scaled_bp, 'yellow', linewidth=2, label=f'Bandpass ({wavelength}d)')

        ax.set_title(f'{wavelength}d - Phase: {result["phase_degrees"]:.1f}° - Smooth: {"YES" if np.std(historical_bp) > 0.5 else "NO"}',
                     color='white', fontsize=12, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.2, color='gray')
        ax.tick_params(colors='white')
        ax.set_ylabel('Price ($)', color='white')

        if idx == len(wavelengths) - 1:
            ax.set_xlabel('Days', color='white')

    except Exception as e:
        print(f"✗ FAILED!")
        print(f"  Error: {str(e)}")
        import traceback
        traceback.print_exc()

plt.tight_layout()
output_file = 'test_new_bandpass_implementation.png'
plt.savefig(output_file, dpi=120, facecolor='black')
print(f"\n{'='*60}")
print(f"Test complete. Output saved: {output_file}")
print("\nCheck if all three wavelengths show smooth sine waves.")
