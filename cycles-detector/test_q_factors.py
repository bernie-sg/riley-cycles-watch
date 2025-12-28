#!/usr/bin/env python3
"""Test different Q factors to find which detects 525d peak"""

import numpy as np
import sys
sys.path.append('algorithms/heatmap')

def create_morlet_with_q(freq, length, q_divisor, q_cap):
    """Create Morlet wavelet with specified Q formula"""
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

def compute_power_with_q(data, wavelength, q_divisor, q_cap):
    """Compute power with specified Q"""
    n = len(data)
    if wavelength > n//2:
        return 0

    freq = 1.0 / wavelength
    cycles = min(8, max(4, n // wavelength))
    wlen = min(n, wavelength * cycles)

    wavelet = create_morlet_with_q(freq, wlen, q_divisor, q_cap)

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

def test_q_factor(prices, q_divisor, q_cap):
    """Test a Q factor and return top peak"""
    # Preprocess
    data = np.log(prices)
    x = np.arange(len(data))
    coeffs = np.polyfit(x, data, 1)
    trend = np.polyval(coeffs, x)
    data = data - trend

    # Scan around 500-550 range with fine resolution
    wavelengths = np.arange(480, 561, 1)
    spectrum = np.array([compute_power_with_q(data, wl, q_divisor, q_cap) for wl in wavelengths])

    # Find peak
    peak_idx = np.argmax(spectrum)
    peak_wl = wavelengths[peak_idx]
    peak_power = spectrum[peak_idx]

    return peak_wl, peak_power

# Load data
prices = np.loadtxt('tlt_prices.txt')
print(f"Testing TLT data ({len(prices)} points)")
print("=" * 60)

# Test range of Q divisors
test_values = [
    (30, 12),
    (35, 12),
    (40, 15),
    (42.94, 15),  # Current
    (50, 15),
    (60, 10),
    (70, 10),
    (80, 10),
    (90, 10),
    (100, 8),
]

print("Q_divisor | Q_cap | Peak Wavelength | Power")
print("-" * 60)

for q_div, q_cap in test_values:
    peak_wl, peak_power = test_q_factor(prices, q_div, q_cap)
    print(f"{q_div:8.2f} | {q_cap:5.0f} | {peak_wl:14d}d | {peak_power:.3f}")

print("\nTarget: ~525d peak (SIGMA-L reference)")