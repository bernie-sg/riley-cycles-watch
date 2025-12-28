#!/usr/bin/env python3
"""
Comprehensive test: Multiple instruments with all their cycles
"""

import requests
import json

def apply_phase_shift(values, shift):
    if shift == 0:
        return values
    return values[shift:] + values[:shift]

def shift_indices(indices, shift_amount, array_length):
    shifted = []
    for idx in indices:
        new_idx = idx + shift_amount
        if new_idx < 0:
            new_idx += array_length
        if new_idx >= array_length:
            new_idx -= array_length
        if 0 <= new_idx < array_length:
            shifted.append(new_idx)
    return shifted

def scale_bandpass(bandpass):
    mean = sum(bandpass) / len(bandpass)
    centered = [v - mean for v in bandpass]
    scale_factor = 0.8
    return [v * scale_factor for v in centered]

def test_all_cycles(symbol):
    print(f"\n{'='*80}")
    print(f"{symbol}")
    print(f"{'='*80}")

    # Get all cycles
    url = f"http://localhost:5001/api/analyze?symbol={symbol}&window_size=4000"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to analyze {symbol}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    data = response.json()
    cycles = data.get('peak_cycles', [])

    if not cycles:
        print(f"❌ No cycles found")
        return False

    wavelengths = [c['wavelength_days'] for c in cycles]
    print(f"Found {len(cycles)} cycles: {wavelengths}")

    all_passed = True

    # Test each cycle
    for i, cycle in enumerate(cycles[:3]):  # Test first 3 cycles max
        wavelength = cycle['wavelength_days']

        url = f"http://localhost:5001/api/bandpass?symbol={symbol}&selected_wavelength={wavelength}&window_size=4000"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"  [{i+1}] {wavelength}d: ❌ Failed to fetch")
                all_passed = False
                continue
        except Exception as e:
            print(f"  [{i+1}] {wavelength}d: ❌ Error: {e}")
            all_passed = False
            continue

        data = response.json()
        raw_bandpass = data['bandpass']['scaled_values']
        backend_peaks = data['bandpass']['peaks']
        backend_troughs = data['bandpass']['troughs']

        # Simulate frontend (with phase_shift=0)
        shifted_bandpass = apply_phase_shift(raw_bandpass, 0)
        scaled_bandpass = scale_bandpass(shifted_bandpass)
        shifted_peaks = shift_indices(backend_peaks, 0, len(raw_bandpass))
        shifted_troughs = shift_indices(backend_troughs, 0, len(raw_bandpass))

        if len(shifted_peaks) == 0:
            print(f"  [{i+1}] {wavelength}d: ❌ No peaks")
            all_passed = False
            continue

        if len(shifted_troughs) == 0:
            print(f"  [{i+1}] {wavelength}d: ❌ No troughs")
            all_passed = False
            continue

        # Check Y-values
        peak_y_values = [scaled_bandpass[idx] for idx in shifted_peaks[:5]]
        trough_y_values = [scaled_bandpass[idx] for idx in shifted_troughs[:5]]
        avg_peak_y = sum(peak_y_values) / len(peak_y_values)
        avg_trough_y = sum(trough_y_values) / len(trough_y_values)

        peak_ok = abs(avg_peak_y - 20) < 5
        trough_ok = abs(avg_trough_y + 20) < 5

        if peak_ok and trough_ok:
            print(f"  [{i+1}] {wavelength}d: ✅ Peak Y={avg_peak_y:.1f}, Trough Y={avg_trough_y:.1f}")
        else:
            print(f"  [{i+1}] {wavelength}d: ❌ Peak Y={avg_peak_y:.1f}, Trough Y={avg_trough_y:.1f}")
            all_passed = False

    return all_passed

# Test key instruments
test_symbols = [
    'IWM',   # Small caps - 2 cycles
    'HON',   # Industrial - multiple cycles
    'AAPL',  # Tech
    'SPY',   # S&P 500
    'TLT',   # Bonds
]

print("="*80)
print("COMPREHENSIVE MULTI-INSTRUMENT TEST")
print("="*80)

results = {}
for symbol in test_symbols:
    try:
        results[symbol] = test_all_cycles(symbol)
    except Exception as e:
        print(f"\n{symbol}: ❌ Exception: {e}")
        results[symbol] = False

print(f"\n{'='*80}")
print("SUMMARY:")
print(f"{'='*80}")
for symbol, passed in results.items():
    status = "✅" if passed else "❌"
    print(f"{status} {symbol}")

passed_count = sum(1 for p in results.values() if p)
failed_count = len(results) - passed_count
print(f"\n{passed_count} passed, {failed_count} failed out of {len(results)} symbols")
print(f"{'='*80}")
