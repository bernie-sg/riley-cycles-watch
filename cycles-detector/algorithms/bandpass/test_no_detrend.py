#!/usr/bin/env python3
"""
Test hypothesis: Maybe we shouldn't detrend at all.
SIGMA-L might apply wavelets directly to log prices without detrending.

The Morlet wavelet naturally extracts the oscillating component.
"""

import sys
sys.path.append('..')
sys.path.append('../..')

import numpy as np
import matplotlib.pyplot as plt
from wavelet_bandpass import compute_wavelet_coefficients, create_high_q_morlet
from data_manager import DataManager

# Load TLT data
dm = DataManager('TLT')
prices, price_df = dm.get_data()

print(f"\nLoaded {len(prices)} TLT prices")

# Use last 2000 points for visualization
recent_prices = prices[-2000:]
wavelength = 470

print(f"\n{'='*60}")
print(f"Testing wavelength: {wavelength}d")
print(f"{'='*60}")

# METHOD 1: Current approach - log + detrend
log_data = np.log(recent_prices)
x = np.arange(len(log_data))
coeffs_poly = np.polyfit(x, log_data, 1)
trend = np.polyval(coeffs_poly, x)
detrended = log_data - trend

complex_coeffs_detrended, _ = compute_wavelet_coefficients(detrended, wavelength, 0.10)
bandpass_detrended = np.real(complex_coeffs_detrended)

print(f"\nMethod 1 (log + detrend):")
print(f"  Mean: {np.mean(bandpass_detrended):.6f}")
print(f"  Std:  {np.std(bandpass_detrended):.6f}")
print(f"  Min:  {np.min(bandpass_detrended):.6f}")
print(f"  Max:  {np.max(bandpass_detrended):.6f}")

# METHOD 2: Just log, no detrend
complex_coeffs_no_detrend, _ = compute_wavelet_coefficients(log_data, wavelength, 0.10)
bandpass_no_detrend = np.real(complex_coeffs_no_detrend)

print(f"\nMethod 2 (log only, NO detrend):")
print(f"  Mean: {np.mean(bandpass_no_detrend):.6f}")
print(f"  Std:  {np.std(bandpass_no_detrend):.6f}")
print(f"  Min:  {np.min(bandpass_no_detrend):.6f}")
print(f"  Max:  {np.max(bandpass_no_detrend):.6f}")

# Plot comparison
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
fig.patch.set_facecolor('black')

# Plot 1: Detrended data with its bandpass
ax1.set_facecolor('black')
ax1.plot(detrended, 'gray', alpha=0.5, linewidth=0.5, label='Detrended Log Price')
ax1.plot(bandpass_detrended * 0.3, 'cyan', linewidth=2, label='Bandpass (detrended)')
ax1.set_title('Method 1: With Detrending', color='white', fontsize=12)
ax1.legend()
ax1.grid(True, alpha=0.2, color='gray')
ax1.tick_params(colors='white')

# Plot 2: Log data (no detrend) with its bandpass
ax2.set_facecolor('black')
ax2.plot(log_data, 'gray', alpha=0.5, linewidth=0.5, label='Log Price (no detrend)')
ax2.plot(bandpass_no_detrend * 0.3 + np.mean(log_data), 'yellow', linewidth=2, label='Bandpass (no detrend)')
ax2.set_title('Method 2: WITHOUT Detrending', color='white', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.2, color='gray')
ax2.tick_params(colors='white')

# Plot 3: Overlay on actual prices - Method 1
ax3.set_facecolor('black')
ax3.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Actual Price')
price_mean = np.mean(recent_prices)
price_range = np.max(recent_prices) - np.min(recent_prices)
scaled_bp1 = bandpass_detrended * (price_range * 0.1) + price_mean
ax3.plot(scaled_bp1, 'cyan', linewidth=2, label='Bandpass (with detrend)')
ax3.set_title('Method 1 on Actual Prices', color='white', fontsize=12)
ax3.legend()
ax3.grid(True, alpha=0.2, color='gray')
ax3.tick_params(colors='white')

# Plot 4: Overlay on actual prices - Method 2
ax4.set_facecolor('black')
ax4.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Actual Price')
scaled_bp2 = bandpass_no_detrend * (price_range * 0.1) + price_mean
ax4.plot(scaled_bp2, 'yellow', linewidth=2, label='Bandpass (no detrend)')
ax4.set_title('Method 2 on Actual Prices', color='white', fontsize=12)
ax4.legend()
ax4.grid(True, alpha=0.2, color='gray')
ax4.tick_params(colors='white')

plt.tight_layout()
plt.savefig('test_detrend_comparison.png', dpi=120, facecolor='black')
print(f"\nSaved: test_detrend_comparison.png")

# Check correlation
correlation = np.corrcoef(bandpass_detrended, bandpass_no_detrend)[0, 1]
print(f"\nCorrelation between methods: {correlation:.6f}")
