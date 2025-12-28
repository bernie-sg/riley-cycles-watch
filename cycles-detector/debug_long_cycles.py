#!/usr/bin/env python3
"""
Debug why long wavelengths (590d, 790d) have detection issues
"""

import requests
import json

def scale_bandpass(bp):
    mean = sum(bp) / len(bp)
    return [(v - mean) * 0.8 for v in bp]

def smooth(signal, window):
    result = []
    for i in range(len(signal)):
        start = max(0, i - window)
        end = min(len(signal), i + window + 1)
        result.append(sum(signal[start:end]) / (end - start))
    return result

def find_peaks(signal, wl):
    dist = wl // 4
    peaks = []
    for i in range(1, len(signal) - 1):
        if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
            peaks.append({'i': i, 'v': signal[i]})

    result = []
    i = 0
    while i < len(peaks):
        end = peaks[i]['i'] + dist
        window = [peaks[i]]
        j = i + 1
        while j < len(peaks) and peaks[j]['i'] < end:
            window.append(peaks[j])
            j += 1
        result.append(max(window, key=lambda p: p['v'])['i'])
        i = j
    return result

def analyze_wavelength(symbol, wavelength):
    """Detailed analysis of one wavelength"""
    print(f"\n{'='*80}")
    print(f"ANALYZING {symbol} {wavelength}d")
    print(f"{'='*80}")

    url = f"http://localhost:5001/api/bandpass?symbol={symbol}&selected_wavelength={wavelength}&window_size=4000"
    r = requests.get(url, timeout=30)
    data = r.json()

    raw_bp = data['bandpass']['scaled_values']
    dates = data['price_data']['dates']

    print(f"Data points: {len(raw_bp)}")
    print(f"Date range: {dates[0]} to {dates[-1]}")

    # Check raw bandpass statistics
    raw_min = min(raw_bp)
    raw_max = max(raw_bp)
    raw_mean = sum(raw_bp) / len(raw_bp)
    print(f"\nRaw bandpass stats:")
    print(f"  Min: {raw_min:.2f}")
    print(f"  Max: {raw_max:.2f}")
    print(f"  Mean: {raw_mean:.2f}")
    print(f"  Range: {raw_max - raw_min:.2f}")

    # Apply frontend scaling
    scaled = scale_bandpass(raw_bp)
    scaled_min = min(scaled)
    scaled_max = max(scaled)
    scaled_mean = sum(scaled) / len(scaled)
    print(f"\nScaled bandpass stats:")
    print(f"  Min: {scaled_min:.2f}")
    print(f"  Max: {scaled_max:.2f}")
    print(f"  Mean: {scaled_mean:.2f}")
    print(f"  Range: {scaled_max - scaled_min:.2f}")

    # Check if smoothing will be applied
    if wavelength > 500:
        smooth_window = wavelength // 20
        print(f"\nSmoothing WILL be applied (window={smooth_window})")
        signal = smooth(scaled, smooth_window)

        smoothed_min = min(signal)
        smoothed_max = max(signal)
        smoothed_mean = sum(signal) / len(signal)
        print(f"Smoothed bandpass stats:")
        print(f"  Min: {smoothed_min:.2f}")
        print(f"  Max: {smoothed_max:.2f}")
        print(f"  Mean: {smoothed_mean:.2f}")
        print(f"  Range: {smoothed_max - smoothed_min:.2f}")
    else:
        print(f"\nSmoothing will NOT be applied")
        signal = scaled

    # Try to detect peaks
    peaks = find_peaks(signal, wavelength)
    print(f"\nPeak detection:")
    print(f"  Distance parameter: {wavelength // 4}")
    print(f"  Peaks found: {len(peaks)}")

    if len(peaks) > 0:
        print(f"\nPeak locations (first 10):")
        for idx in peaks[:10]:
            print(f"  Index {idx}: Date={dates[idx]}, Y={scaled[idx]:.2f}")

        # Calculate actual spacing between peaks
        if len(peaks) > 1:
            spacings = [peaks[i+1] - peaks[i] for i in range(len(peaks)-1)]
            avg_spacing = sum(spacings) / len(spacings)
            print(f"\nPeak spacing analysis:")
            print(f"  Expected: {wavelength} bars")
            print(f"  Actual average: {avg_spacing:.1f} bars")
            print(f"  Error: {abs(avg_spacing - wavelength) / wavelength * 100:.1f}%")
            print(f"  All spacings: {[int(s) for s in spacings[:5]]}...")
    else:
        print("  ❌ NO PEAKS DETECTED")

        # Let's check why - look for ANY local maxima
        print("\nLooking for ANY local maxima in the signal...")
        all_maxima = []
        for i in range(1, len(signal) - 1):
            if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
                all_maxima.append({'i': i, 'v': signal[i]})

        print(f"  Total local maxima found: {len(all_maxima)}")
        if len(all_maxima) > 0:
            print(f"  First 10 maxima:")
            for m in all_maxima[:10]:
                print(f"    Index {m['i']}: Y={m['v']:.3f}")

        # Check signal smoothness (derivative)
        print("\nChecking signal smoothness (slopes)...")
        slopes = []
        for i in range(1, min(100, len(signal))):
            slopes.append(signal[i] - signal[i-1])
        avg_slope = sum(abs(s) for s in slopes) / len(slopes)
        max_slope = max(abs(s) for s in slopes)
        print(f"  Average slope magnitude: {avg_slope:.6f}")
        print(f"  Max slope magnitude: {max_slope:.6f}")

# Test the problematic wavelengths
analyze_wavelength('ZC=F', 540)  # This works (reference)
analyze_wavelength('ZC=F', 590)  # This has issues
analyze_wavelength('ZC=F', 790)  # This has issues
