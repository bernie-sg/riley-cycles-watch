#!/usr/bin/env python3
"""
Test what the ACTUAL wavelet bandpass looks like (no sine wave generation)
"""
import numpy as np
import matplotlib.pyplot as plt
from data_manager import DataManager
from algorithms.bandpass.wavelet_bandpass import compute_wavelet_coefficients

# Load TLT
dm = DataManager('TLT')
prices, _ = dm.get_data()

print(f"\nLoaded {len(prices)} TLT prices")

# Preprocess
log_data = np.log(prices)
x = np.arange(len(log_data))
coeffs = np.polyfit(x, log_data, 1)
trend = np.polyval(coeffs, x)
detrended = log_data - trend

wavelengths = [350, 470, 625]

fig, axes = plt.subplots(len(wavelengths), 1, figsize=(16, 12))
fig.patch.set_facecolor('black')

for idx, wavelength in enumerate(wavelengths):
    print(f"\n{'='*60}")
    print(f"Testing wavelength: {wavelength}d")

    # Get wavelet coefficients
    complex_coeffs, weights = compute_wavelet_coefficients(detrended, wavelength, 0.10)

    # The bandpass IS the real part
    bandpass = np.real(complex_coeffs)

    print(f"Bandpass min: {np.min(bandpass):.6f}")
    print(f"Bandpass max: {np.max(bandpass):.6f}")
    print(f"Bandpass std: {np.std(bandpass):.6f}")

    # Plot
    ax = axes[idx]
    ax.set_facecolor('black')

    # Show last 1500 bars
    recent_prices = prices[-1500:]
    recent_bandpass = bandpass[-1500:]

    # Scale bandpass to price range
    price_mean = np.mean(recent_prices)
    price_range = np.max(recent_prices) - np.min(recent_prices)

    # Normalize bandpass to ±1 range first
    bp_std = np.std(recent_bandpass)
    if bp_std > 0:
        normalized_bp = recent_bandpass / (bp_std * 3)  # ±3 sigma
    else:
        normalized_bp = recent_bandpass

    scaled_bp = normalized_bp * (price_range * 0.1) + price_mean

    ax.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Price')
    ax.plot(scaled_bp, 'yellow', linewidth=2, label=f'Actual Bandpass ({wavelength}d)')

    ax.set_title(f'{wavelength}d - Actual Wavelet Bandpass Output',
                 color='white', fontsize=12, fontweight='bold')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.2, color='gray')
    ax.tick_params(colors='white')
    ax.set_ylabel('Price ($)', color='white')

    if idx == len(wavelengths) - 1:
        ax.set_xlabel('Days', color='white')

plt.tight_layout()
output_file = 'actual_bandpass_test.png'
plt.savefig(output_file, dpi=120, facecolor='black')
print(f"\n{'='*60}")
print(f"Saved: {output_file}")
print("This shows the ACTUAL wavelet bandpass output (no sine wave generation)")
