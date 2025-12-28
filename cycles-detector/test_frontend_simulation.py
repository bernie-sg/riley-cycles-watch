#!/usr/bin/env python3
"""
Simulate frontend processing to identify the label positioning bug
"""

import requests
import json
import numpy as np

def apply_phase_shift(values, shift):
    """Simulate frontend applyPhaseShift"""
    if shift == 0:
        return values
    return values[shift:] + values[:shift]

def scale_bandpass(bandpass):
    """Simulate frontend centering and scaling"""
    mean = sum(bandpass) / len(bandpass)
    centered = [v - mean for v in bandpass]
    scale_factor = 0.8
    scaled = [v * scale_factor for v in centered]
    return scaled

def find_peaks(signal, wavelength):
    """Simulate frontend findPeaks"""
    distance = wavelength // 4

    # Find all local maxima
    all_peaks = []
    for i in range(1, len(signal) - 1):
        if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
            all_peaks.append({'idx': i, 'value': signal[i]})

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

def find_troughs(signal, wavelength):
    """Simulate frontend findTroughs"""
    distance = wavelength // 4

    # Find all local minima
    all_troughs = []
    for i in range(1, len(signal) - 1):
        if signal[i] < signal[i-1] and signal[i] < signal[i+1]:
            all_troughs.append({'idx': i, 'value': signal[i]})

    # Filter by distance
    filtered_troughs = []
    i = 0
    while i < len(all_troughs):
        window_end = all_troughs[i]['idx'] + distance
        window = [all_troughs[i]]
        j = i + 1
        while j < len(all_troughs) and all_troughs[j]['idx'] < window_end:
            window.append(all_troughs[j])
            j += 1

        best = min(window, key=lambda p: p['value'])
        filtered_troughs.append(best['idx'])
        i = j

    return filtered_troughs

def test_wavelength(symbol, wavelength):
    """Test a specific wavelength and show what annotations would be created"""
    print(f"\n{'='*80}")
    print(f"Testing {symbol} - {wavelength}d cycle")
    print(f"{'='*80}")

    url = f"http://localhost:5001/api/bandpass?symbol={symbol}&selected_wavelength={wavelength}&window_size=4000"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"ERROR: HTTP {response.status_code}")
        return

    data = response.json()

    # Extract data like frontend does
    raw_bandpass = data['bandpass']['scaled_values']
    dates = data['price_data']['dates']

    print(f"\n1. RAW BACKEND DATA:")
    print(f"   Wavelength: {data['bandpass']['wavelength']}d")
    print(f"   Data length: {len(dates)}")
    print(f"   Raw bandpass length: {len(raw_bandpass)}")
    print(f"   Raw bandpass range: {min(raw_bandpass):.2f} to {max(raw_bandpass):.2f}")

    # Simulate frontend processing
    phase_shift = 0  # Default phase shift
    shifted_bandpass = apply_phase_shift(raw_bandpass, phase_shift)
    scaled_bandpass = scale_bandpass(shifted_bandpass)

    print(f"\n2. FRONTEND PROCESSING (same as JavaScript):")
    print(f"   Phase shift applied: {phase_shift}")
    print(f"   Scaled bandpass length: {len(scaled_bandpass)}")
    print(f"   Scaled bandpass range: {min(scaled_bandpass):.2f} to {max(scaled_bandpass):.2f}")
    print(f"   Expected range: ~±20 (backend sends ±25, frontend scales by 0.8)")

    if abs(max(scaled_bandpass)) < 15:
        print(f"   ⚠️  WARNING: Scaled range is too small! Should be ±20, got ±{max(abs(min(scaled_bandpass)), abs(max(scaled_bandpass))):.1f}")

    # Detect peaks and troughs
    wavelength_val = data['bandpass']['wavelength']
    peak_indices = find_peaks(scaled_bandpass, wavelength_val)
    trough_indices = find_troughs(scaled_bandpass, wavelength_val)

    print(f"\n3. PEAK/TROUGH DETECTION:")
    print(f"   Peaks found: {len(peak_indices)}")
    print(f"   Troughs found: {len(trough_indices)}")

    if len(peak_indices) == 0:
        print("   ❌ ERROR: NO PEAKS FOUND!")
        return

    if len(trough_indices) == 0:
        print("   ❌ ERROR: NO TROUGHS FOUND!")
        return

    # Show first 5 peak annotations
    print(f"\n4. FIRST 5 PEAK ANNOTATIONS (what would appear on chart):")
    for i, idx in enumerate(peak_indices[:5]):
        date = dates[idx]
        y_value = scaled_bandpass[idx]
        print(f"   Peak {i+1}: date={date}, y={y_value:.2f}, idx={idx}")
        if abs(y_value) < 15:
            print(f"           ⚠️  Y-value is too low! Should be ~+20")

    # Show first 5 trough annotations
    print(f"\n5. FIRST 5 TROUGH ANNOTATIONS (what would appear on chart):")
    for i, idx in enumerate(trough_indices[:5]):
        date = dates[idx]
        y_value = scaled_bandpass[idx]
        print(f"   Trough {i+1}: date={date}, y={y_value:.2f}, idx={idx}")
        if abs(y_value) < 15:
            print(f"           ⚠️  Y-value is too low! Should be ~-20")

    # Analyze the problem
    print(f"\n6. DIAGNOSIS:")
    peak_y_values = [scaled_bandpass[idx] for idx in peak_indices[:5]]
    trough_y_values = [scaled_bandpass[idx] for idx in trough_indices[:5]]

    avg_peak = sum(peak_y_values) / len(peak_y_values) if peak_y_values else 0
    avg_trough = sum(trough_y_values) / len(trough_y_values) if trough_y_values else 0

    print(f"   Average peak Y-value: {avg_peak:.2f} (expected: ~+20)")
    print(f"   Average trough Y-value: {avg_trough:.2f} (expected: ~-20)")

    if abs(avg_peak - 20) > 5:
        print(f"   ❌ PROBLEM: Peak Y-values are incorrect!")
        print(f"      Expected: ~+20, Got: {avg_peak:.2f}")
        print(f"      This is why labels appear at wrong Y positions")
    else:
        print(f"   ✅ Peak Y-values look correct")

    if abs(abs(avg_trough) - 20) > 5:
        print(f"   ❌ PROBLEM: Trough Y-values are incorrect!")
        print(f"      Expected: ~-20, Got: {avg_trough:.2f}")
        print(f"      This is why labels appear at wrong Y positions")
    else:
        print(f"   ✅ Trough Y-values look correct")

def main():
    print("="*80)
    print("FRONTEND SIMULATION TEST - Finding Label Position Bug")
    print("="*80)
    print("\nThis simulates exactly what the frontend JavaScript does:")
    print("1. Fetch bandpass data from backend")
    print("2. Apply phase shift (default: 0)")
    print("3. Center and scale bandpass (scale by 0.8)")
    print("4. Detect peaks and troughs")
    print("5. Create annotations with Y-values from scaled_bandpass[idx]")
    print("\nIf Y-values are wrong, we'll see it here.")

    # Test both wavelengths that user reported issues with
    test_wavelength('IWM', 380)
    test_wavelength('IWM', 515)

if __name__ == '__main__':
    main()
