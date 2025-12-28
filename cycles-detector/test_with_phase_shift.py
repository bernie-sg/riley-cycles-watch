#!/usr/bin/env python3
"""
Test peak positioning with phase shift applied
"""

import requests
import json

def apply_phase_shift(values, shift):
    """JavaScript applyPhaseShift equivalent"""
    if shift == 0:
        return values
    return values[shift:] + values[:shift]

def shift_peak_trough_indices(indices, shift_amount, array_length):
    """JavaScript shiftPeakTroughIndices equivalent"""
    shifted = []
    for idx in indices:
        new_idx = idx + shift_amount
        # Wrap around if needed
        if new_idx < 0:
            new_idx += array_length
        if new_idx >= array_length:
            new_idx -= array_length
        if 0 <= new_idx < array_length:
            shifted.append(new_idx)
    return shifted

def scale_bandpass(bandpass):
    """Frontend scaling: center at zero and scale by 0.8"""
    mean = sum(bandpass) / len(bandpass)
    centered = [v - mean for v in bandpass]
    scale_factor = 0.8
    scaled = [v * scale_factor for v in centered]
    return scaled

def test_wavelength(symbol, wavelength, phase_shift=0):
    print(f"\n{'='*80}")
    print(f"Testing {symbol} - {wavelength}d with phase_shift={phase_shift}")
    print(f"{'='*80}")

    url = f"http://localhost:5001/api/bandpass?symbol={symbol}&selected_wavelength={wavelength}&window_size=4000"
    response = requests.get(url)
    data = response.json()

    raw_bandpass = data['bandpass']['scaled_values']
    backend_peaks = data['bandpass']['peaks']
    backend_troughs = data['bandpass']['troughs']
    dates = data['price_data']['dates']

    print(f"\n1. BACKEND DATA:")
    print(f"   Bandpass length: {len(raw_bandpass)}")
    print(f"   Backend peaks: {len(backend_peaks)}")
    print(f"   Backend troughs: {len(backend_troughs)}")

    # Simulate frontend processing
    print(f"\n2. FRONTEND PROCESSING:")

    # Step 1: Apply phase shift to bandpass
    shifted_bandpass = apply_phase_shift(raw_bandpass, phase_shift)
    print(f"   Applied phase shift: {phase_shift}")

    # Step 2: Scale the bandpass
    scaled_bandpass = scale_bandpass(shifted_bandpass)
    print(f"   Scaled bandpass range: {min(scaled_bandpass):.2f} to {max(scaled_bandpass):.2f}")

    # Step 3: Shift peak indices
    shifted_peak_indices = shift_peak_trough_indices(backend_peaks, phase_shift, len(raw_bandpass))
    shifted_trough_indices = shift_peak_trough_indices(backend_troughs, phase_shift, len(raw_bandpass))
    print(f"   Shifted peaks: {len(shifted_peak_indices)}")
    print(f"   Shifted troughs: {len(shifted_trough_indices)}")

    # Check Y-values at shifted peak indices
    print(f"\n3. Y-VALUES AT SHIFTED PEAK INDICES:")
    if len(shifted_peak_indices) > 0:
        peak_y_values = [scaled_bandpass[idx] for idx in shifted_peak_indices[:5]]
        avg_peak_y = sum(peak_y_values) / len(peak_y_values)
        print(f"   First 5 shifted peaks:")
        for i, idx in enumerate(shifted_peak_indices[:5]):
            print(f"   Peak {i+1}: idx={idx}, date={dates[idx]}, Y={scaled_bandpass[idx]:.2f}")

        print(f"\n4. Y-VALUES AT SHIFTED TROUGH INDICES:")
        if len(shifted_trough_indices) > 0:
            trough_y_values = [scaled_bandpass[idx] for idx in shifted_trough_indices[:5]]
            avg_trough_y = sum(trough_y_values) / len(trough_y_values)
            print(f"   First 5 shifted troughs:")
            for i, idx in enumerate(shifted_trough_indices[:5]):
                print(f"   Trough {i+1}: idx={idx}, date={dates[idx]}, Y={scaled_bandpass[idx]:.2f}")

        print(f"\n5. DIAGNOSIS:")
        print(f"   Average peak Y: {avg_peak_y:.2f} (expected ~+20)")
        print(f"   Average trough Y: {avg_trough_y:.2f} (expected ~-20)")

        peak_ok = abs(avg_peak_y - 20) < 5
        trough_ok = abs(avg_trough_y + 20) < 5

        if peak_ok and trough_ok:
            print(f"   ✅ CORRECT - Labels will appear at peaks/troughs at ±20")
            return True
        else:
            print(f"   ❌ WRONG - Y-values incorrect")
            return False
    else:
        print(f"   ❌ No peaks after shifting")
        return False

# Test with phase shift = 0 (default)
print("="*80)
print("TESTING WITH PHASE SHIFT = 0 (DEFAULT)")
print("="*80)

results = []
results.append(("IWM", 380, test_wavelength('IWM', 380, 0)))
results.append(("IWM", 515, test_wavelength('IWM', 515, 0)))

print(f"\n{'='*80}")
print(f"RESULTS:")
for symbol, wl, passed in results:
    status = "✅" if passed else "❌"
    print(f"{status} {symbol} {wl}d")
print(f"{'='*80}")
