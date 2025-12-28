#!/usr/bin/env python3
"""
Test hybrid approach: frontend detection with backend fallback
"""

import requests

def scale_bandpass(bandpass):
    mean = sum(bandpass) / len(bandpass)
    centered = [v - mean for v in bandpass]
    scale_factor = 0.8
    return [v * scale_factor for v in centered]

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
    backend_peaks = data['bandpass']['peaks']
    dates = data['price_data']['dates']

    # Simulate frontend
    scaled_bandpass = scale_bandpass(raw_bandpass)
    frontend_peaks = find_peaks(scaled_bandpass, wavelength)

    # Hybrid approach
    if len(frontend_peaks) == 0:
        peak_indices = backend_peaks
        method = "BACKEND (fallback)"
    else:
        peak_indices = frontend_peaks
        method = "FRONTEND"

    # Find peaks in visible range (2021-2027)
    visible_peaks = [dates[idx] for idx in peak_indices if '2021' <= dates[idx] <= '2027']

    print(f"\n{symbol} {wavelength}d:")
    print(f"  Method: {method}")
    print(f"  Frontend detected: {len(frontend_peaks)} peaks")
    print(f"  Using: {len(peak_indices)} peaks")
    print(f"  Visible peaks (2021-2027): {visible_peaks[:3]}")

    # Check Y-values
    if len(peak_indices) > 0:
        sample_y = [scaled_bandpass[idx] for idx in peak_indices[:5]]
        avg_y = sum(sample_y) / len(sample_y)
        ok = abs(avg_y - 20) < 5
        print(f"  Average Y: {avg_y:.2f} {'✅' if ok else '❌'}")
        return ok
    return False

print("="*60)
print("HYBRID APPROACH TEST")
print("="*60)

results = {}
results['IWM 380d'] = test_symbol('IWM', 380)
results['IWM 515d'] = test_symbol('IWM', 515)

print(f"\n{'='*60}")
print("RESULTS:")
for name, passed in results.items():
    print(f"{'✅' if passed else '❌'} {name}")
print(f"{'='*60}")
