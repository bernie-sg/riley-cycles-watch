#!/usr/bin/env python3
"""
Test bandpass generation and create visual output
"""
import numpy as np
import matplotlib.pyplot as plt
from data_manager import DataManager
from algorithms.bandpass.pure_sine_bandpass import create_pure_sine_bandpass

# Load TLT
dm = DataManager('TLT')
prices, _ = dm.get_data()

print(f"\nLoaded {len(prices)} TLT prices")

# Test with the three problematic wavelengths
wavelengths = [350, 470, 625]

fig, axes = plt.subplots(len(wavelengths), 1, figsize=(16, 12))
fig.patch.set_facecolor('black')

for idx, wavelength in enumerate(wavelengths):
    print(f"\n{'='*60}")
    print(f"Testing wavelength: {wavelength}d")

    result = create_pure_sine_bandpass(
        prices,
        wavelength,
        bandwidth_pct=0.10,
        extend_future=700
    )

    print(f"Phase: {result['phase_degrees']:.1f}°")
    print(f"Amplitude: {result['amplitude']:.6f}")
    print(f"Bandpass length: {len(result['bandpass_normalized'])}")

    # Plot
    ax = axes[idx]
    ax.set_facecolor('black')

    # Show last 1500 bars
    recent_prices = prices[-1500:]
    recent_bandpass = result['bandpass_normalized'][-2200:-700]  # Historical part only

    # Scale bandpass to price range
    price_mean = np.mean(recent_prices)
    price_range = np.max(recent_prices) - np.min(recent_prices)
    scaled_bp = recent_bandpass * (price_range * 0.1) + price_mean

    ax.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Price')
    ax.plot(scaled_bp, 'yellow', linewidth=2, label=f'Bandpass ({wavelength}d)')

    ax.set_title(f'{wavelength}d - Phase: {result["phase_degrees"]:.1f}° - Amp: {result["amplitude"]:.6f}',
                 color='white', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.2, color='gray')
    ax.tick_params(colors='white')
    ax.set_ylabel('Price ($)', color='white')

    if idx == len(wavelengths) - 1:
        ax.set_xlabel('Days', color='white')

plt.tight_layout()
output_file = 'bandpass_visual_test.png'
plt.savefig(output_file, dpi=120, facecolor='black')
print(f"\n{'='*60}")
print(f"Saved: {output_file}")
print("Please check if all three wavelengths show smooth sine waves.")
