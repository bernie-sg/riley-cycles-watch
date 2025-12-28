#!/usr/bin/env python3
"""
Test detecting peaks from RAW bandpass (before scaling)
"""

import requests
import json

def find_peaks(signal, wavelength):
    distance = wavelength // 4
    all_peaks = []
    for i in range(1, len(signal) - 1):
        if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
            all_peaks.append({'idx': i, 'value': signal[i]})

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

def scale_bandpass(bandpass):
    mean = sum(bandpass) / len(bandpass)
    centered = [v - mean for v in bandpass]
    scale_factor = 0.8
    scaled = [v * scale_factor for v in centered]
    return scaled

def test_wavelength(symbol, wavelength):
    print(f"\n{'='*80}")
    print(f"Testing {symbol} - {wavelength}d")
    print(f"{'='*80}")

    url = f"http://localhost:5001/api/bandpass?symbol={symbol}&selected_wavelength={wavelength}&window_size=4000"
    response = requests.get(url)
    data = response.json()

    raw_bandpass = data['bandpass']['scaled_values']
    wavelength_val = data['bandpass']['wavelength']
    dates = data['price_data']['dates']

    print(f"\n1. RAW BANDPASS (from backend):")
    print(f"   Range: {min(raw_bandpass):.2f} to {max(raw_bandpass):.2f}")

    # Detect from RAW
    raw_peaks = find_peaks(raw_bandpass, wavelength_val)
    print(f"\n2. PEAKS DETECTED FROM RAW BANDPASS: {len(raw_peaks)}")

    # Now scale the bandpass
    scaled_bandpass = scale_bandpass(raw_bandpass)
    print(f"\n3. SCALED BANDPASS:")
    print(f"   Range: {min(scaled_bandpass):.2f} to {max(scaled_bandpass):.2f}")

    # Check Y-values at the peak indices
    if len(raw_peaks) > 0:
        print(f"\n4. Y-VALUES AT PEAK INDICES:")
        print(f"   Using indices from raw bandpass detection")
        for i, idx in enumerate(raw_peaks[:5]):
            raw_y = raw_bandpass[idx]
            scaled_y = scaled_bandpass[idx]
            date = dates[idx]
            print(f"   Peak {i+1}: idx={idx}, date={date}")
            print(f"            raw_y={raw_y:.2f}, scaled_y={scaled_y:.2f}")

        print(f"\n5. DIAGNOSIS:")
        avg_scaled_y = sum(scaled_bandpass[idx] for idx in raw_peaks[:5]) / min(5, len(raw_peaks))
        print(f"   Average scaled Y at peaks: {avg_scaled_y:.2f}")
        print(f"   Expected: ~+20")

        if abs(avg_scaled_y - 20) < 5:
            print(f"   ✅ Correct - labels will appear at peaks (~+20)")
        else:
            print(f"   ❌ Wrong - labels will appear at {avg_scaled_y:.1f} instead of ~+20")

test_wavelength('IWM', 380)
test_wavelength('IWM', 515)
