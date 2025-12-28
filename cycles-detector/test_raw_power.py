#!/usr/bin/env python3
"""
Test RAW power spectrum without any post-processing
"""

import numpy as np
from scipy.signal import find_peaks

def create_high_q_morlet(freq, length):
    """EXACT scanner_clean Morlet wavelet"""
    Q = 15.0 + 50.0 * freq
    sigma = Q / (2.0 * np.pi * freq)

    t = np.arange(length) - length/2.0
    envelope = np.exp(-t**2 / (2.0 * sigma**2))
    carrier = np.exp(1j * 2.0 * np.pi * freq * t)
    wavelet = envelope * carrier

    norm = np.sqrt(np.sum(np.abs(wavelet)**2))
    wavelet /= norm

    return wavelet

def compute_power_raw(data, wavelength):
    """RAW power computation without averaging"""
    n = len(data)
    if wavelength > n//2:
        return 0

    freq = 1.0 / wavelength
    cycles = min(8, max(4, n // wavelength))
    wlen = min(n, wavelength * cycles)

    wavelet = create_high_q_morlet(freq, wlen)

    total_power = 0
    count = 0
    step = max(1, wavelength // 8)

    for center in range(wlen//2, n - wlen//2 + 1, step):
        start_idx = center - wlen//2
        end_idx = start_idx + wlen

        if start_idx >= 0 and end_idx <= n:
            signal_segment = data[start_idx:end_idx]
            conv = np.sum(signal_segment * np.conj(wavelet))
            total_power += np.abs(conv)**2
            count += 1

    return np.sqrt(total_power / count) if count > 0 else 0

# Load TLT data
prices = np.loadtxt('tlt_prices.txt')
print(f"Loaded {len(prices)} TLT prices")

window_size = 5689
wavelengths = np.arange(100, 801, 5)

data = prices[-window_size:]

# Log + detrend
data_log = np.log(data)
x = np.arange(len(data_log))
coeffs = np.polyfit(x, data_log, 1)
trend = np.polyval(coeffs, x)
data_detrended = data_log - trend

print("\n" + "="*60)
print("RAW POWER SPECTRUM (no post-processing)")
print("="*60)

# Compute spectrum WITHOUT any processing
spectrum_raw = np.array([compute_power_raw(data_detrended, wl) for wl in wavelengths])

# Normalize
spectrum_raw = spectrum_raw / np.max(spectrum_raw)

# Find peaks
peaks, props = find_peaks(spectrum_raw, height=0.1, distance=5)
sorted_peaks = peaks[np.argsort(spectrum_raw[peaks])[::-1]]

print("\nTop 10 detected cycles (RAW, no processing):")
for i, peak_idx in enumerate(sorted_peaks[:10]):
    wl = wavelengths[peak_idx]
    power = spectrum_raw[peak_idx]
    cal_days = wl * 1.451
    print(f"  {i+1}. {cal_days:.0f} calendar days ({wl:.0f} trading days) - Power: {power:.3f}")

print("\n" + "="*60)
print("SIGMA-L REFERENCE: 526 calendar days")
print("="*60)