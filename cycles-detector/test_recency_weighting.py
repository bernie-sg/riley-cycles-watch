#!/usr/bin/env python3
"""
Test SIGMA-L's recency weighting approach
Two spectra: full window + recent window, combined
"""

import numpy as np
from scipy.signal import find_peaks

def create_high_q_morlet(freq, length):
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
print(f"Loaded {len(prices)} TLT prices\n")

window_size = 5689
wavelengths = np.arange(100, 801, 5)

# Full window
data_full = prices[-window_size:]
data_full_log = np.log(data_full)
data_full_log = data_full_log - np.mean(data_full_log)

# Recent window (last 25% - "recency marker")
recency_size = window_size // 4
data_recent = prices[-recency_size:]
data_recent_log = np.log(data_recent)
data_recent_log = data_recent_log - np.mean(data_recent_log)

print("="*70)
print("FULL WINDOW SPECTRUM")
print("="*70)
spectrum_full = np.array([compute_power_raw(data_full_log, wl) for wl in wavelengths])
spectrum_full = spectrum_full / np.max(spectrum_full)

peaks_full, _ = find_peaks(spectrum_full, height=0.1, distance=5)
sorted_peaks_full = peaks_full[np.argsort(spectrum_full[peaks_full])[::-1]]

for i, peak_idx in enumerate(sorted_peaks_full[:5]):
    wl = wavelengths[peak_idx]
    cal_days = wl * 1.451
    power = spectrum_full[peak_idx]
    print(f"  {i+1}. {cal_days:4.0f} cal days - Power: {power:.3f}")

print("\n" + "="*70)
print("RECENT WINDOW SPECTRUM (last 25%)")
print("="*70)
spectrum_recent = np.array([compute_power_raw(data_recent_log, wl) for wl in wavelengths])
spectrum_recent = spectrum_recent / np.max(spectrum_recent)

peaks_recent, _ = find_peaks(spectrum_recent, height=0.1, distance=5)
sorted_peaks_recent = peaks_recent[np.argsort(spectrum_recent[peaks_recent])[::-1]]

for i, peak_idx in enumerate(sorted_peaks_recent[:5]):
    wl = wavelengths[peak_idx]
    cal_days = wl * 1.451
    power = spectrum_recent[peak_idx]
    print(f"  {i+1}. {cal_days:4.0f} cal days - Power: {power:.3f}")

print("\n" + "="*70)
print("COMBINED SPECTRUM (Full * 0.4 + Recent * 0.6)")
print("="*70)
# Weight recent data more heavily
spectrum_combined = 0.4 * spectrum_full + 0.6 * spectrum_recent
spectrum_combined = spectrum_combined / np.max(spectrum_combined)

peaks_combined, _ = find_peaks(spectrum_combined, height=0.1, distance=5)
sorted_peaks_combined = peaks_combined[np.argsort(spectrum_combined[peaks_combined])[::-1]]

for i, peak_idx in enumerate(sorted_peaks_combined[:5]):
    wl = wavelengths[peak_idx]
    cal_days = wl * 1.451
    power = spectrum_combined[peak_idx]
    marker = " ← TARGET!" if 500 <= cal_days <= 550 else ""
    print(f"  {i+1}. {cal_days:4.0f} cal days - Power: {power:.3f}{marker}")

print("\n" + "="*70)
print("SIGMA-L TARGET: 526 calendar days")
print("="*70)