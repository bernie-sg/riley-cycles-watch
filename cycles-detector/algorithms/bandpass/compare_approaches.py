#!/usr/bin/env python3
"""
Compare V6 (wavelet output) vs V7 (pure sine) approaches
"""

import sys
sys.path.append('..')
sys.path.append('../..')

import numpy as np
import matplotlib.pyplot as plt
from wavelet_bandpass import create_wavelet_bandpass_filter
from pure_sine_bandpass import create_pure_sine_bandpass
from data_manager import DataManager

# Load TLT
dm = DataManager('TLT')
prices, _ = dm.get_data()

print(f"\nLoaded {len(prices)} TLT prices")

# Test all three wavelengths the user mentioned
wavelengths = [350, 470, 625]

fig, axes = plt.subplots(len(wavelengths), 2, figsize=(18, 12))
fig.patch.set_facecolor('black')

for idx, wavelength in enumerate(wavelengths):
    # V6 approach
    v6_result = create_wavelet_bandpass_filter(
        prices,
        wavelength,
        bandwidth_pct=0.10,
        extend_future=700
    )

    # V7 approach
    v7_result = create_pure_sine_bandpass(
        prices,
        wavelength,
        bandwidth_pct=0.10,
        extend_future=700
    )

    print(f"\n{wavelength}d:")
    print(f"  V6 phase: {v6_result['phase_degrees']:.1f}°")
    print(f"  V7 phase: {v7_result['phase_degrees']:.1f}°")
    print(f"  V6 amplitude: {v6_result['amplitude']:.6f}")
    print(f"  V7 amplitude: {v7_result['amplitude']:.6f}")

    recent_prices = prices[-1500:]
    price_mean = np.mean(recent_prices)
    price_range = np.max(recent_prices) - np.min(recent_prices)

    # Plot V6
    ax_v6 = axes[idx, 0]
    ax_v6.set_facecolor('black')
    ax_v6.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Price')

    v6_bandpass = v6_result['bandpass_normalized'][-1500:]
    scaled_v6 = v6_bandpass * (price_range * 0.1) + price_mean
    ax_v6.plot(scaled_v6, 'cyan', linewidth=2, label=f'V6 ({wavelength}d)')

    ax_v6.set_title(f'V6: {wavelength}d - Phase: {v6_result["phase_degrees"]:.1f}°',
                    color='white', fontsize=12, fontweight='bold')
    ax_v6.legend(loc='upper left')
    ax_v6.grid(True, alpha=0.2, color='gray')
    ax_v6.tick_params(colors='white')
    ax_v6.set_ylabel('Price ($)', color='white')

    # Plot V7
    ax_v7 = axes[idx, 1]
    ax_v7.set_facecolor('black')
    ax_v7.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Price')

    v7_bandpass = v7_result['bandpass_normalized'][-1500:]
    scaled_v7 = v7_bandpass * (price_range * 0.1) + price_mean
    ax_v7.plot(scaled_v7, 'yellow', linewidth=2, label=f'V7 Pure Sine ({wavelength}d)')

    ax_v7.set_title(f'V7: {wavelength}d - Phase: {v7_result["phase_degrees"]:.1f}°',
                    color='white', fontsize=12, fontweight='bold')
    ax_v7.legend(loc='upper left')
    ax_v7.grid(True, alpha=0.2, color='gray')
    ax_v7.tick_params(colors='white')
    ax_v7.set_ylabel('Price ($)', color='white')

    if idx == len(wavelengths) - 1:
        ax_v6.set_xlabel('Days', color='white')
        ax_v7.set_xlabel('Days', color='white')

plt.tight_layout()
plt.savefig('v6_vs_v7_comparison.png', dpi=150, facecolor='black')
print(f"\nSaved: v6_vs_v7_comparison.png")
print("\nV7 should show perfectly smooth sine waves for ALL wavelengths.")
print("V6 may show modulated/irregular waves (especially visible on 350d and 625d).")
