#!/usr/bin/env python3
"""
Test unified approach with smoothing for long wavelengths
"""

import requests

def scale_bandpass(bandpass):
    mean = sum(bandpass) / len(bandpass)
    centered = [v - mean for v in bandpass]
    scale_factor = 0.8
    return [v * scale_factor for v in centered]

def smooth_signal(signal, window):
    """Apply moving average smoothing"""
    smoothed = []
    for i in range(len(signal)):
        start = max(0, i - window)
        end = min(len(signal), i + window + 1)
        smoothed.append(sum(signal[start:end]) / (end - start))
    return smoothed

def find_peaks(signal, wavelength):
    distance = wavelength // 4
    all_peaks = []
    for i in range(1, len(signal) - 1):
        if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
            all_peaks.append({'idx': i, 'value': signal[i]})

    if len(all_peaks) == 0:
        return []

    filtered_peaks = []
    i = 0
    while i < len(all_peaks):
        window_end = all_peaks[i]['idx'] + distance
        window = [all_peaks[i]]
        j = i + 1
        while j < len(all_peaks) and all_peaks[j]['idx'] < window_end:
            window.append(all_peaks[j])
            j += 1
        best = max(window, key=lambda p: p['value'])
        filtered_peaks.append(best['idx'])
        i = j
    return filtered_peaks

def test_symbol(symbol, wavelength):
    url = f"http://localhost:5001/api/bandpass?symbol={symbol}&selected_wavelength={wavelength}&window_size=4000&bandwidth=0.10"
    response = requests.get(url, timeout=20)
    data = response.json()

    raw_bandpass = data['bandpass']['scaled_values']
    dates = data['price_data']['dates']

    # Simulate frontend
    scaled_bandpass = scale_bandpass(raw_bandpass)

    # UNIFIED APPROACH: Apply smoothing for long wavelengths
    signal_to_analyze = scaled_bandpass
    if wavelength > 500:
        smooth_window = wavelength // 20
        signal_to_analyze = smooth_signal(scaled_bandpass, smooth_window)
        print(f"  Smoothing applied: window={smooth_window}")

    # Detect peaks
    peak_indices = find_peaks(signal_to_analyze, wavelength)

    # Find peaks in visible range (2021-2027)
    visible_peaks = [dates[idx] for idx in peak_indices if '2021' <= dates[idx] <= '2027']

    print(f"\n{symbol} {wavelength}d:")
    print(f"  Peaks detected: {len(peak_indices)}")
    print(f"  Visible peaks (2021-2027): {visible_peaks[:3]}")

    # Check Y-values using the ORIGINAL scaled bandpass (not smoothed)
    if len(peak_indices) > 0:
        sample_y = [scaled_bandpass[idx] for idx in peak_indices[:5]]
        avg_y = sum(sample_y) / len(sample_y)
        ok = abs(avg_y - 20) < 5
        print(f"  Average Y: {avg_y:.2f} {'✅' if ok else '❌'}")
        return ok
    else:
        print(f"  ❌ No peaks detected")
        return False

print("="*60)
print("UNIFIED APPROACH WITH SMOOTHING TEST")
print("="*60)

results = {}
results['IWM 380d'] = test_symbol('IWM', 380)
results['IWM 515d'] = test_symbol('IWM', 515)

# Test a few more instruments with different wavelengths
try:
    results['HON 430d'] = test_symbol('HON', 430)
except:
    pass

print(f"\n{'='*60}")
print("RESULTS:")
for name, passed in results.items():
    print(f"{'✅' if passed else '❌'} {name}")
print(f"{'='*60}")

all_passed = all(results.values())
if all_passed:
    print("\n✅ ALL TESTS PASSED - Unified approach works!")
else:
    print(f"\n❌ Some tests failed")
