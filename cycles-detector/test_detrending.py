#!/usr/bin/env python3
"""
Test different detrending methods to see which gives 526-day cycle as dominant
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
    """RAW power computation"""
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
print(f"Price range: {prices.min():.2f} - {prices.max():.2f}")

window_size = 5689
wavelengths = np.arange(100, 801, 5)
data = prices[-window_size:]
data_log = np.log(data)
x = np.arange(len(data_log))

detrending_methods = [
    ("No detrending", None),
    ("Mean centering", "mean"),
    ("Linear (degree 1)", 1),
    ("Quadratic (degree 2)", 2),
    ("Cubic (degree 3)", 3),
    ("Quartic (degree 4)", 4),
]

print("\n" + "="*70)
print("TESTING DIFFERENT DETRENDING METHODS")
print("="*70)

for method_name, degree in detrending_methods:
    print(f"\n{method_name}:")
    print("-" * 70)

    if degree is None:
        data_detrended = data_log
    elif degree == "mean":
        data_detrended = data_log - np.mean(data_log)
    else:
        coeffs = np.polyfit(x, data_log, degree)
        trend = np.polyval(coeffs, x)
        data_detrended = data_log - trend

    # Compute spectrum
    spectrum = np.array([compute_power_raw(data_detrended, wl) for wl in wavelengths])
    spectrum = spectrum / np.max(spectrum)

    # Find peaks
    peaks, _ = find_peaks(spectrum, height=0.1, distance=5)
    sorted_peaks = peaks[np.argsort(spectrum[peaks])[::-1]]

    # Show top 5
    for i, peak_idx in enumerate(sorted_peaks[:5]):
        wl = wavelengths[peak_idx]
        cal_days = wl * 1.451
        power = spectrum[peak_idx]
        marker = " ← CLOSE!" if 500 <= cal_days <= 550 else ""
        print(f"  {i+1}. {cal_days:4.0f} cal days ({wl:3.0f} trading) - Power: {power:.3f}{marker}")

print("\n" + "="*70)
print("SIGMA-L TARGET: 526 calendar days (363 trading days)")
print("="*70)