#!/usr/bin/env python3
"""
Detect peaks from the displayed (scaled) bandpass to see where they actually are
"""

import requests
import json

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

    # Filter by distance
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

# Test 380d
url = "http://localhost:5001/api/bandpass?symbol=IWM&selected_wavelength=380&window_size=4000&bandwidth=0.10"
response = requests.get(url)
data = response.json()

raw_bandpass = data['bandpass']['scaled_values']
dates = data['price_data']['dates']
backend_peaks = data['bandpass']['peaks']
wavelength = data['bandpass']['wavelength']

# Simulate frontend: scale the bandpass
scaled_bandpass = scale_bandpass(raw_bandpass)

# Detect peaks from scaled bandpass
frontend_peaks = find_peaks(scaled_bandpass, wavelength)

print("380d Cycle Analysis:")
print(f"Backend peaks: {len(backend_peaks)}")
print(f"Frontend-detected peaks: {len(frontend_peaks)}")
print()

# Compare first 10 peaks in 2021-2027 range
print("Backend peaks in 2021-2027:")
for idx in backend_peaks:
    if '2021' <= dates[idx] <= '2027':
        print(f"  {dates[idx]}")

print()
print("Frontend-detected peaks in 2021-2027:")
for idx in frontend_peaks:
    if '2021' <= dates[idx] <= '2027':
        y = scaled_bandpass[idx]
        print(f"  {dates[idx]}, Y={y:.2f}")
