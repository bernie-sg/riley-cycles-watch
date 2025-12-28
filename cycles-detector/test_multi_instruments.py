#!/usr/bin/env python3
"""
Test multiple instruments with all their cycles
"""

import requests
import json

def scale_bandpass(bandpass):
    mean = sum(bandpass) / len(bandpass)
    centered = [v - mean for v in bandpass]
    scale_factor = 0.8
    scaled = [v * scale_factor for v in centered]
    return scaled

def test_all_cycles_for_symbol(symbol):
    print(f"\n{'='*80}")
    print(f"Testing {symbol}")
    print(f"{'='*80}")

    # Get initial analysis to find all cycles
    url = f"http://localhost:5001/api/analyze?symbol={symbol}&window_size=4000"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Failed to analyze {symbol}")
        return False

    data = response.json()
    cycles = data.get('peak_cycles', [])

    if not cycles:
        print(f"❌ No cycles found for {symbol}")
        return False

    wavelengths = [c['wavelength_days'] for c in cycles]
    print(f"\nFound {len(cycles)} cycles: {wavelengths}")

    all_passed = True

    # Test each cycle
    for i, cycle in enumerate(cycles):
        wavelength = cycle['wavelength_days']
        print(f"\n  [{i+1}/{len(cycles)}] Testing {wavelength}d cycle...")

        url = f"http://localhost:5001/api/bandpass?symbol={symbol}&selected_wavelength={wavelength}&window_size=4000"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"    ❌ Failed to fetch bandpass for {wavelength}d")
            all_passed = False
            continue

        data = response.json()
        raw_bandpass = data['bandpass']['scaled_values']
        backend_peaks = data['bandpass']['peaks']
        backend_troughs = data['bandpass']['troughs']

        if len(backend_peaks) == 0:
            print(f"    ❌ No peaks provided by backend")
            all_passed = False
            continue

        if len(backend_troughs) == 0:
            print(f"    ❌ No troughs provided by backend")
            all_passed = False
            continue

        # Test Y-values
        scaled_bandpass = scale_bandpass(raw_bandpass)

        peak_y_values = [scaled_bandpass[idx] for idx in backend_peaks[:5] if idx < len(scaled_bandpass)]
        if not peak_y_values:
            print(f"    ❌ No valid peak indices")
            all_passed = False
            continue

        avg_peak_y = sum(peak_y_values) / len(peak_y_values)

        if abs(avg_peak_y - 20) < 5:
            print(f"    ✅ {wavelength}d: {len(backend_peaks)} peaks, {len(backend_troughs)} troughs, avg Y={avg_peak_y:.1f}")
        else:
            print(f"    ❌ {wavelength}d: Wrong Y-values (avg={avg_peak_y:.1f}, expected ~±20)")
            all_passed = False

    return all_passed

# Test multiple instruments
test_symbols = [
    'IWM',   # Small caps - 2 cycles
    'HON',   # Industrial
    'AAPL',  # Tech
    'SPY',   # S&P 500
    'TLT',   # Bonds
    'GLD',   # Gold
    'XLE',   # Energy
    'JPM',   # Banking
]

print("="*80)
print("MULTI-INSTRUMENT COMPREHENSIVE TEST")
print("="*80)
print("\nTesting backend peaks/troughs approach across multiple instruments")
print("Goal: Verify ALL cycles for ALL instruments show correct Y-values")

passed = 0
failed = 0

for symbol in test_symbols:
    try:
        if test_all_cycles_for_symbol(symbol):
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print(f"\n❌ {symbol}: Exception - {e}")
        failed += 1

print(f"\n{'='*80}")
print(f"FINAL RESULTS: {passed} passed, {failed} failed out of {len(test_symbols)} symbols")
print(f"{'='*80}")

if failed == 0:
    print("\n✅ ALL TESTS PASSED - Backend peaks/troughs work correctly for all cycles!")
else:
    print(f"\n❌ {failed} symbol(s) failed - review issues above")
