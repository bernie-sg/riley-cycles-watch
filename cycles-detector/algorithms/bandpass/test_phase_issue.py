#!/usr/bin/env python3
"""
Test to demonstrate phase alignment issue

The problem: We're using np.real(complex_coeffs) which gives us the
real part of the wavelet output, but this doesn't necessarily align
properly with the price data.

Solution: Use the magnitude and instantaneous phase from the complex
coefficients to reconstruct a properly aligned sine wave.
"""

import sys
sys.path.append('..')
sys.path.append('../..')

import numpy as np
import matplotlib.pyplot as plt
from wavelet_bandpass import compute_wavelet_coefficients
from data_manager import DataManager

# Load TLT data
dm = DataManager('TLT')
prices, price_df = dm.get_data()

print(f"\nLoaded {len(prices)} TLT prices")

# Use last 2000 points for visualization
recent_prices = prices[-2000:]
wavelength = 470

# Preprocess: log-transform and detrend
log_data = np.log(recent_prices)
x = np.arange(len(log_data))
coeffs_poly = np.polyfit(x, log_data, 1)
trend = np.polyval(coeffs_poly, x)
detrended = log_data - trend

# Compute complex wavelet coefficients
complex_coeffs, weights = compute_wavelet_coefficients(detrended, wavelength, 0.10)

# METHOD 1: Current approach - just take real part
method1_bandpass = np.real(complex_coeffs)

# METHOD 2: Use magnitude and instantaneous phase
magnitude = np.abs(complex_coeffs)
instantaneous_phase = np.angle(complex_coeffs)

# Generate sine wave using instantaneous phase at each point
t = np.arange(len(recent_prices))
omega = 2 * np.pi / wavelength

# For each point, use the instantaneous phase
method2_bandpass = magnitude * np.cos(instantaneous_phase)

print(f"\n{'='*60}")
print(f"Testing wavelength: {wavelength}d")
print(f"{'='*60}")

print(f"\nMethod 1 (current - np.real):")
print(f"  Mean: {np.mean(method1_bandpass):.6f}")
print(f"  Std:  {np.std(method1_bandpass):.6f}")
print(f"  Min:  {np.min(method1_bandpass):.6f}")
print(f"  Max:  {np.max(method1_bandpass):.6f}")

print(f"\nMethod 2 (magnitude * cos(phase)):")
print(f"  Mean: {np.mean(method2_bandpass):.6f}")
print(f"  Std:  {np.std(method2_bandpass):.6f}")
print(f"  Min:  {np.min(method2_bandpass):.6f}")
print(f"  Max:  {np.max(method2_bandpass):.6f}")

print(f"\nAre they the same? {np.allclose(method1_bandpass, method2_bandpass, atol=0.001)}")
correlation = np.corrcoef(method1_bandpass, method2_bandpass)[0, 1]
print(f"Correlation: {correlation:.6f}")

# Plot comparison
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 10))
fig.patch.set_facecolor('black')

# Plot 1: Detrended price with Method 1
ax1.set_facecolor('black')
ax1.plot(detrended, 'gray', alpha=0.5, linewidth=0.5, label='Detrended Price')
ax1.plot(method1_bandpass * 0.02, 'cyan', linewidth=2, label='Method 1: np.real()')
ax1.set_title('Method 1: Current Approach (np.real)', color='white', fontsize=12)
ax1.legend()
ax1.grid(True, alpha=0.2, color='gray')
ax1.tick_params(colors='white')

# Plot 2: Detrended price with Method 2
ax2.set_facecolor('black')
ax2.plot(detrended, 'gray', alpha=0.5, linewidth=0.5, label='Detrended Price')
ax2.plot(method2_bandpass * 0.02, 'yellow', linewidth=2, label='Method 2: mag*cos(phase)')
ax2.set_title('Method 2: Magnitude × cos(phase)', color='white', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.2, color='gray')
ax2.tick_params(colors='white')

# Plot 3: Instantaneous phase
ax3.set_facecolor('black')
ax3.plot(instantaneous_phase, 'lime', linewidth=1, label='Instantaneous Phase')
ax3.set_title('Instantaneous Phase from Complex Coefficients', color='white', fontsize=12)
ax3.set_ylabel('Phase (radians)', color='white')
ax3.legend()
ax3.grid(True, alpha=0.2, color='gray')
ax3.tick_params(colors='white')

# Plot 4: Magnitude
ax4.set_facecolor('black')
ax4.plot(magnitude, 'magenta', linewidth=1, label='Magnitude')
ax4.set_title('Magnitude from Complex Coefficients', color='white', fontsize=12)
ax4.set_ylabel('Magnitude', color='white')
ax4.legend()
ax4.grid(True, alpha=0.2, color='gray')
ax4.tick_params(colors='white')

plt.tight_layout()
plt.savefig('test_phase_methods.png', dpi=120, facecolor='black')
print(f"\nSaved: test_phase_methods.png")
