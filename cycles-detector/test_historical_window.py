#!/usr/bin/env python3
"""Test if using historical data window matches SIGMA-L"""

import numpy as np
from scipy.ndimage import gaussian_filter1d

def create_morlet(freq, length, q_divisor=70, q_cap=10):
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

def compute_power(data, wavelength, q_divisor=70, q_cap=10):
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
print(f"Full dataset: {len(prices)} points")
print()

# Test different historical endpoints
test_windows = [
    5688,  # SIGMA-L sample size
    5600,
    5500,
    5400,
    5200,
    5000,
]

print("Testing different historical windows:")
print("=" * 70)
print(f"{'Window Size':<15} {'Top Peak':<15} {'2nd Peak':<15} {'3rd Peak':<15}")
print("-" * 70)

for window_size in test_windows:
    if window_size > len(prices):
        continue

    # Use most recent N points
    test_prices = prices[-window_size:]

    # Preprocess
    data = np.log(test_prices)
    x = np.arange(len(data))
    coeffs = np.polyfit(x, data, 1)
    trend = np.polyval(coeffs, x)
    data = data - trend

    # Compute spectrum
    wavelengths = np.arange(100, 801, 1)
    spectrum = np.array([compute_power(data, wl, 70, 10) for wl in wavelengths])

    # Find top 3 peaks
    top3_idx = np.argsort(spectrum)[-3:][::-1]
    top3_wl = [wavelengths[i] for i in top3_idx]
    top3_power = [spectrum[i] for i in top3_idx]

    print(f"{window_size:<15} {top3_wl[0]}d ({top3_power[0]:.2f}){'':<4} "
          f"{top3_wl[1]}d ({top3_power[1]:.2f}){'':<4} {top3_wl[2]}d ({top3_power[2]:.2f})")

print("\nTarget: ~525d as dominant peak (SIGMA-L)")