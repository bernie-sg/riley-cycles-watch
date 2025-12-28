#!/usr/bin/env python3
"""
Test using backend peaks directly
"""

import requests
import json

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
    backend_peaks = data['bandpass']['peaks']
    backend_troughs = data['bandpass']['troughs']
    dates = data['price_data']['dates']

    print(f"\n1. BACKEND DATA:")
    print(f"   Peaks provided: {len(backend_peaks)}")
    print(f"   Troughs provided: {len(backend_troughs)}")

    # Scale the bandpass like frontend does
    scaled_bandpass = scale_bandpass(raw_bandpass)

    print(f"\n2. USING BACKEND PEAKS AS INDICES:")
    if len(backend_peaks) > 0:
        print(f"   First 5 backend peaks:")
        for i, idx in enumerate(backend_peaks[:5]):
            if idx < len(scaled_bandpass):
                raw_y = raw_bandpass[idx]
                scaled_y = scaled_bandpass[idx]
                date = dates[idx] if idx < len(dates) else "OUT OF RANGE"
                print(f"   Peak {i+1}: idx={idx}, date={date}")
                print(f"            raw_y={raw_y:.2f}, scaled_y={scaled_y:.2f}")
            else:
                print(f"   Peak {i+1}: idx={idx} OUT OF RANGE (max={len(scaled_bandpass)})")

        avg_y = sum(scaled_bandpass[idx] for idx in backend_peaks[:5] if idx < len(scaled_bandpass)) / min(5, len([idx for idx in backend_peaks[:5] if idx < len(scaled_bandpass)]))
        print(f"\n3. DIAGNOSIS:")
        print(f"   Average Y at backend peaks: {avg_y:.2f}")
        print(f"   Expected: ~+20")

        if abs(avg_y - 20) < 5:
            print(f"   ✅ Backend peaks would give correct Y positions")
        else:
            print(f"   ❌ Backend peaks give wrong Y positions: {avg_y:.1f} instead of ~+20")

test_wavelength('IWM', 380)
test_wavelength('IWM', 515)
