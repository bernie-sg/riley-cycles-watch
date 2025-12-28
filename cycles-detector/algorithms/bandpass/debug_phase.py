#!/usr/bin/env python3
"""
Debug phase alignment - compare wavelet vs pure sine
"""

import sys
sys.path.append('..')
sys.path.append('../..')

import numpy as np
import matplotlib.pyplot as plt
from wavelet_bandpass import create_wavelet_bandpass_filter
from data_manager import DataManager

# Load TLT data
dm = DataManager('TLT')
prices, price_df = dm.get_data()

print(f"Loaded {len(prices)} TLT prices")

# Use last 2000 points for visualization
recent_prices = prices[-2000:]
wavelength = 350

# Get wavelet bandpass
result = create_wavelet_bandpass_filter(
    recent_prices,
    wavelength,
    bandwidth_pct=0.10,
    extend_future=0
)

wavelet_bp = result['bandpass_normalized']
wavelet_phase = result['phase_radians']

print(f"\nWavelet Bandpass:")
print(f"  Phase: {result['phase_degrees']:.1f}°")
print(f"  Amplitude: {result['amplitude']:.6f}")

# Generate pure sine wave with same phase for comparison
t = np.arange(len(recent_prices))
omega = 2 * np.pi / wavelength
pure_sine = np.sin(omega * t + wavelet_phase)

# Plot comparison
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(16, 10))
fig.patch.set_facecolor('black')

# Detrend prices for better visualization
log_prices = np.log(recent_prices)
x = np.arange(len(log_prices))
coeffs = np.polyfit(x, log_prices, 1)
trend = np.polyval(coeffs, x)
detrended = log_prices - trend

# Plot 1: Detrended price with wavelet bandpass
ax1.set_facecolor('black')
ax1.plot(detrended, 'gray', alpha=0.5, linewidth=0.5, label='Detrended Price')
ax1.plot(wavelet_bp * 0.02, 'cyan', linewidth=2, label='Wavelet Bandpass')
ax1.set_title('Detrended Price vs Wavelet Bandpass', color='white', fontsize=12)
ax1.legend()
ax1.grid(True, alpha=0.2, color='gray')
ax1.tick_params(colors='white')

# Plot 2: Detrended price with pure sine
ax2.set_facecolor('black')
ax2.plot(detrended, 'gray', alpha=0.5, linewidth=0.5, label='Detrended Price')
ax2.plot(pure_sine * 0.02, 'yellow', linewidth=2, label=f'Pure Sine (phase={result["phase_degrees"]:.1f}°)')
ax2.set_title('Detrended Price vs Pure Sine Wave', color='white', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.2, color='gray')
ax2.tick_params(colors='white')

# Plot 3: Wavelet BP vs Pure Sine overlay
ax3.set_facecolor('black')
ax3.plot(wavelet_bp, 'cyan', linewidth=2, alpha=0.7, label='Wavelet Bandpass')
ax3.plot(pure_sine, 'yellow', linewidth=2, alpha=0.7, linestyle='--', label='Pure Sine')
ax3.set_title('Wavelet Bandpass vs Pure Sine Wave', color='white', fontsize=12)
ax3.legend()
ax3.grid(True, alpha=0.2, color='gray')
ax3.tick_params(colors='white')

plt.tight_layout()
plt.savefig('debug_phase_alignment.png', dpi=120, facecolor='black')
print("\nSaved: debug_phase_alignment.png")

# Check if they're the same
correlation = np.corrcoef(wavelet_bp, pure_sine)[0, 1]
print(f"\nCorrelation between wavelet and pure sine: {correlation:.6f}")
print(f"Are they identical? {np.allclose(wavelet_bp, pure_sine, atol=0.01)}")

if correlation > 0.99:
    print("\n⚠️  WARNING: Wavelet bandpass is nearly identical to pure sine wave!")
    print("   This means we're not actually using the wavelet coefficients properly.")
