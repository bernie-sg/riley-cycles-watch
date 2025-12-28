#!/usr/bin/env python3
"""
Phase Diagnostic - Show me what different phases look like
So I can understand what's wrong
"""

import sys
sys.path.append('..')
sys.path.append('../..')

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from wavelet_bandpass import compute_wavelet_coefficients
from wavelet_bandpass_optimized import create_optimized_bandpass
from data_manager import DataManager

# Load TLT
dm = DataManager('TLT')
prices, _ = dm.get_data()

print(f"\nLoaded {len(prices)} TLT prices")

# Use recent data
recent_prices = prices[-1000:]
wavelength = 470

print(f"Wavelength: {wavelength}d")

# Get optimized result
result = create_optimized_bandpass(prices, wavelength, 0.10, 0)

print(f"\nOptimized phase: {result['phase_degrees']:.1f}°")
print(f"Alignment score: {result['alignment_score']:.3f}")

# Detrend for peak finding
log_prices = np.log(recent_prices)
x = np.arange(len(log_prices))
coeffs = np.polyfit(x, log_prices, 1)
trend = np.polyval(coeffs, x)
detrended = log_prices - trend

# Find actual price peaks and troughs
min_distance = int(wavelength * 0.4)
price_peaks, _ = find_peaks(detrended, distance=min_distance, prominence=0.01)
price_troughs, _ = find_peaks(-detrended, distance=min_distance, prominence=0.01)

print(f"\nFound {len(price_peaks)} peaks and {len(price_troughs)} troughs in recent data")
print(f"Peak indices: {price_peaks}")
print(f"Trough indices: {price_troughs}")

# Get bandpass
bandpass = result['bandpass_normalized'][-1000:]

# Find sine peaks and troughs
sine_peaks, _ = find_peaks(bandpass, distance=min_distance)
sine_troughs, _ = find_peaks(-bandpass, distance=min_distance)

print(f"\nSine wave has {len(sine_peaks)} peaks and {len(sine_troughs)} troughs")
print(f"Sine peak indices: {sine_peaks}")
print(f"Sine trough indices: {sine_troughs}")

# Calculate alignment errors
print(f"\n{'='*60}")
print(f"ALIGNMENT ANALYSIS")
print(f"{'='*60}")

for i, price_peak in enumerate(price_peaks):
    if len(sine_peaks) > 0:
        distances = np.abs(sine_peaks - price_peak)
        closest_idx = np.argmin(distances)
        closest_sine_peak = sine_peaks[closest_idx]
        error_days = closest_sine_peak - price_peak
        error_phase = (error_days / wavelength) * 360
        print(f"Price Peak #{i+1} @ {price_peak}: Sine peak @ {closest_sine_peak}, Error = {error_days:+d} days ({error_phase:+.1f}°)")

print()
for i, price_trough in enumerate(price_troughs):
    if len(sine_troughs) > 0:
        distances = np.abs(sine_troughs - price_trough)
        closest_idx = np.argmin(distances)
        closest_sine_trough = sine_troughs[closest_idx]
        error_days = closest_sine_trough - price_trough
        error_phase = (error_days / wavelength) * 360
        print(f"Price Trough #{i+1} @ {price_trough}: Sine trough @ {closest_sine_trough}, Error = {error_days:+d} days ({error_phase:+.1f}°)")

# Plot with markers
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(18, 10))
fig.patch.set_facecolor('black')

# Plot 1: Price with peaks/troughs marked
ax1.set_facecolor('black')
ax1.plot(recent_prices, 'white', alpha=0.7, linewidth=1, label='Price')

# Mark price peaks and troughs
for peak in price_peaks:
    ax1.plot(peak, recent_prices[peak], 'ro', markersize=10, label='Price Peak' if peak == price_peaks[0] else '')
for trough in price_troughs:
    ax1.plot(trough, recent_prices[trough], 'go', markersize=10, label='Price Trough' if trough == price_troughs[0] else '')

# Overlay sine wave (scaled)
price_mean = np.mean(recent_prices)
price_range = np.max(recent_prices) - np.min(recent_prices)
scaled_bandpass = bandpass * (price_range * 0.1) + price_mean
ax1.plot(scaled_bandpass, 'yellow', linewidth=2, alpha=0.8, label='Sine Wave')

# Mark sine peaks and troughs
for peak in sine_peaks:
    ax1.plot(peak, scaled_bandpass[peak], 'r^', markersize=12, markeredgecolor='white', markeredgewidth=1)
for trough in sine_troughs:
    ax1.plot(trough, scaled_bandpass[trough], 'gv', markersize=12, markeredgecolor='white', markeredgewidth=1)

ax1.set_title(f'TLT {wavelength}d - Phase: {result["phase_degrees"]:.1f}° - Score: {result["alignment_score"]:.3f}',
              color='white', fontsize=14, fontweight='bold')
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.2, color='gray')
ax1.tick_params(colors='white')
ax1.set_ylabel('Price ($)', color='white', fontsize=12)

# Plot 2: Normalized bandpass with peaks/troughs
ax2.set_facecolor('black')
ax2.plot(bandpass, 'yellow', linewidth=2, label='Normalized Sine Wave')
ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)

# Mark sine peaks and troughs
for peak in sine_peaks:
    ax2.plot(peak, bandpass[peak], 'r^', markersize=12, markeredgecolor='white', markeredgewidth=1, label='Sine Peak' if peak == sine_peaks[0] else '')
for trough in sine_troughs:
    ax2.plot(trough, bandpass[trough], 'gv', markersize=12, markeredgecolor='white', markeredgewidth=1, label='Sine Trough' if trough == sine_troughs[0] else '')

# Mark where price peaks/troughs are (as vertical lines)
for peak in price_peaks:
    ax2.axvline(peak, color='red', alpha=0.3, linestyle=':', linewidth=1)
for trough in price_troughs:
    ax2.axvline(trough, color='green', alpha=0.3, linestyle=':', linewidth=1)

ax2.set_title('Normalized Sine Wave (dotted lines = price extremes)', color='white', fontsize=14)
ax2.legend(loc='upper left')
ax2.grid(True, alpha=0.2, color='gray')
ax2.tick_params(colors='white')
ax2.set_ylabel('Normalized Amplitude', color='white', fontsize=12)
ax2.set_xlabel('Days (recent 1000)', color='white', fontsize=12)

plt.tight_layout()
plt.savefig('phase_diagnostic.png', dpi=150, facecolor='black')
print(f"\nSaved: phase_diagnostic.png")
print(f"\nPlease review this image to see where the alignment is failing.")
