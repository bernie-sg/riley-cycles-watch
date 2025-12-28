#!/usr/bin/env python3
"""Test high-pass filter to suppress long cycles before wavelet analysis"""

import numpy as np
from scipy.ndimage import gaussian_filter1d

def simple_moving_average(data, period):
    """Simple moving average"""
    return np.convolve(data, np.ones(period)/period, mode='same')

def high_pass_filter(data, cutoff_period):
    """High-pass filter: remove cycles longer than cutoff

    data - signal - low_pass(signal) = high_pass signal
    """
    # Low-pass filter (moving average)
    low_pass = simple_moving_average(data, cutoff_period)

    # High-pass = original - low_pass
    high_pass = data - low_pass

    return high_pass

def create_morlet(freq, length, q_divisor=42.94, q_cap=15):
    wavelength = 1.0 / freq
    Q = min(wavelength / q_divisor, q_cap)
    sigma = Q / (2.0 * np.pi * freq)

    t = np.arange(length) - length/2.0
    envelope = np.exp(-t**2 / (2.0 * sigma**2))
    carrier = np.exp(1j * 2.0 * np.pi * freq * t)
    wavelet = envelope * carrier

    norm = np.sqrt(np.sum(np.abs(wavelet)**2))
    wavelet /= norm
    return wavelet

def compute_power(data, wavelength, q_divisor=42.94, q_cap=15):
    n = len(data)
    if wavelength > n//2:
        return 0

    freq = 1.0 / wavelength
    cycles = min(8, max(4, n // wavelength))
    wlen = min(n, wavelength * cycles)
    wavelet = create_morlet(freq, wlen, q_divisor, q_cap)

    max_power = 0
    step = max(1, wavelength // 8)

    for center in range(wlen//2, n - wlen//2 + 1, step):
        start_idx = center - wlen//2
        end_idx = start_idx + wlen

        if start_idx >= 0 and end_idx <= n:
            signal_segment = data[start_idx:end_idx]
            conv = np.sum(signal_segment * np.conj(wavelet))
            power = np.abs(conv)**2
            max_power = max(max_power, power)

    return np.sqrt(max_power) if max_power > 0 else 0

# Load data
prices = np.loadtxt('tlt_prices.txt')
print(f"Loaded {len(prices)} price points")
print()

# Test different high-pass cutoffs
cutoffs_to_test = [500, 550, 600, 650, 700, 750, 800]

print("=" * 80)
print("HIGH-PASS FILTER TEST - Effect on Peak Detection")
print("=" * 80)
print(f"{'Cutoff':<10} {'1st Peak':<15} {'2nd Peak':<15} {'3rd Peak':<15}")
print("-" * 80)

for cutoff in cutoffs_to_test:
    # Preprocess
    data = np.log(prices)

    # Apply high-pass filter BEFORE detrending
    data_highpass = high_pass_filter(data, cutoff)

    # Simple linear detrend on the high-passed data
    x = np.arange(len(data_highpass))
    coeffs = np.polyfit(x, data_highpass, 1)
    trend = np.polyval(coeffs, x)
    data_final = data_highpass - trend

    # Compute spectrum
    wavelengths = np.arange(100, 801, 1)
    spectrum = np.array([compute_power(data_final, wl, 42.94, 15) for wl in wavelengths])

    # Find top 3 peaks
    top3_idx = np.argsort(spectrum)[-3:][::-1]
    top3_wl = [wavelengths[i] for i in top3_idx]
    top3_power = [spectrum[i] for i in top3_idx]

    print(f"{cutoff}d{'':<6} {top3_wl[0]}d ({top3_power[0]:.2f}){'':<4} "
          f"{top3_wl[1]}d ({top3_power[1]:.2f}){'':<4} {top3_wl[2]}d ({top3_power[2]:.2f})")

print()
print("Target: 525d as dominant peak")
print("Expected: Cutoffs around 650-700d should suppress 760d and reveal 525d")