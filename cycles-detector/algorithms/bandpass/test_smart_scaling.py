#!/usr/bin/env python3
"""
Test hypothesis: Maybe the scaling factor should match the actual cycle amplitude
in the detrended price data, not just be a fixed percentage of price range.

SIGMA-L might be:
1. Extract bandpass from detrended log prices (gives us the cycle component)
2. Scale this bandpass to match the amplitude of cycles in the ACTUAL log prices
3. Add back to price mean to overlay on chart

This way, the sine wave amplitude naturally matches the price swing amplitude.
"""

import sys
sys.path.append('..')
sys.path.append('../..')

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from wavelet_bandpass import compute_wavelet_coefficients
from data_manager import DataManager

# Load TLT data
dm = DataManager('TLT')
prices, price_df = dm.get_data()

print(f"\nLoaded {len(prices)} TLT prices")

# Use last 1500 points for better visualization
recent_prices = prices[-1500:]
wavelength = 470

print(f"\n{'='*60}")
print(f"Testing wavelength: {wavelength}d")
print(f"{'='*60}")

# Standard approach: log + detrend
log_prices = np.log(recent_prices)
x = np.arange(len(log_prices))
coeffs_poly = np.polyfit(x, log_prices, 1)
trend = np.polyval(coeffs_poly, x)
detrended = log_prices - trend

# Get wavelet bandpass
complex_coeffs, _ = compute_wavelet_coefficients(detrended, wavelength, 0.10)
bandpass_normalized = np.real(complex_coeffs)

# Normalize to ±1
if np.std(bandpass_normalized) > 0:
    bandpass_normalized = bandpass_normalized / np.std(bandpass_normalized)

print(f"\nBandpass (normalized):")
print(f"  Mean: {np.mean(bandpass_normalized):.6f}")
print(f"  Std:  {np.std(bandpass_normalized):.6f}")
print(f"  Min:  {np.min(bandpass_normalized):.6f}")
print(f"  Max:  {np.max(bandpass_normalized):.6f}")

# METHOD 1: Current approach - fixed % of price range
price_mean = np.mean(recent_prices)
price_range = np.max(recent_prices) - np.min(recent_prices)
scaled_bandpass_method1 = bandpass_normalized * (price_range * 0.10) + price_mean

print(f"\nMethod 1 (10% of price range):")
print(f"  Scale factor: {price_range * 0.10:.4f}")
print(f"  Min: ${np.min(scaled_bandpass_method1):.2f}")
print(f"  Max: ${np.max(scaled_bandpass_method1):.2f}")
print(f"  Range: ${np.max(scaled_bandpass_method1) - np.min(scaled_bandpass_method1):.2f}")

# METHOD 2: Match amplitude to actual detrended price oscillations
# Measure the amplitude of oscillations in detrended log prices
detrended_amplitude = np.std(detrended)
scaled_bandpass_method2 = bandpass_normalized * detrended_amplitude

# Convert back to price space: exp(log_price + bandpass) ≈ price * exp(bandpass)
# For small bandpass: price * (1 + bandpass)
# Better approach: add to log prices then exp
log_with_bandpass = np.mean(log_prices) + scaled_bandpass_method2
prices_method2 = np.exp(log_with_bandpass)

print(f"\nMethod 2 (match detrended amplitude):")
print(f"  Detrended amplitude: {detrended_amplitude:.6f}")
print(f"  Min: ${np.min(prices_method2):.2f}")
print(f"  Max: ${np.max(prices_method2):.2f}")
print(f"  Range: ${np.max(prices_method2) - np.min(prices_method2):.2f}")

# METHOD 3: Bandpass filter the log prices directly to see natural amplitude
# Use a proper bandpass filter on log prices
nyquist = 0.5  # samples per day
low = 1.0 / (wavelength * 1.1)  # 10% bandwidth
high = 1.0 / (wavelength * 0.9)
sos = signal.butter(4, [low, high], 'bandpass', fs=1.0, output='sos')
filtered_log = signal.sosfiltfilt(sos, log_prices)
prices_method3 = np.exp(filtered_log + np.mean(log_prices))

print(f"\nMethod 3 (Butterworth bandpass on log):")
print(f"  Min: ${np.min(prices_method3):.2f}")
print(f"  Max: ${np.max(prices_method3):.2f}")
print(f"  Range: ${np.max(prices_method3) - np.min(prices_method3):.2f}")

# Plot comparison
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
fig.patch.set_facecolor('black')

# Plot 1: Method 1 - Fixed % of range
ax1.set_facecolor('black')
ax1.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Actual Price')
ax1.plot(scaled_bandpass_method1, 'cyan', linewidth=2, label='Sine Wave (10% range)')
ax1.set_title('Method 1: Fixed 10% of Price Range', color='white', fontsize=12)
ax1.set_ylabel('Price ($)', color='white')
ax1.legend()
ax1.grid(True, alpha=0.2, color='gray')
ax1.tick_params(colors='white')

# Plot 2: Method 2 - Match detrended amplitude
ax2.set_facecolor('black')
ax2.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Actual Price')
ax2.plot(prices_method2, 'yellow', linewidth=2, label='Sine Wave (matched amplitude)')
ax2.set_title('Method 2: Match Detrended Amplitude', color='white', fontsize=12)
ax2.set_ylabel('Price ($)', color='white')
ax2.legend()
ax2.grid(True, alpha=0.2, color='gray')
ax2.tick_params(colors='white')

# Plot 3: Method 3 - Butterworth filter
ax3.set_facecolor('black')
ax3.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Actual Price')
ax3.plot(prices_method3, 'lime', linewidth=2, label='Butterworth Bandpass')
ax3.set_title('Method 3: Butterworth Bandpass Filter', color='white', fontsize=12)
ax3.set_ylabel('Price ($)', color='white')
ax3.legend()
ax3.grid(True, alpha=0.2, color='gray')
ax3.tick_params(colors='white')

# Plot 4: All three overlaid
ax4.set_facecolor('black')
ax4.plot(recent_prices, 'white', alpha=0.3, linewidth=0.5, label='Actual Price')
ax4.plot(scaled_bandpass_method1, 'cyan', linewidth=1.5, alpha=0.7, label='Method 1')
ax4.plot(prices_method2, 'yellow', linewidth=1.5, alpha=0.7, label='Method 2')
ax4.plot(prices_method3, 'lime', linewidth=1.5, alpha=0.7, label='Method 3')
ax4.set_title('All Methods Comparison', color='white', fontsize=12)
ax4.set_ylabel('Price ($)', color='white')
ax4.legend()
ax4.grid(True, alpha=0.2, color='gray')
ax4.tick_params(colors='white')

plt.tight_layout()
plt.savefig('test_smart_scaling.png', dpi=120, facecolor='black')
print(f"\nSaved: test_smart_scaling.png")
