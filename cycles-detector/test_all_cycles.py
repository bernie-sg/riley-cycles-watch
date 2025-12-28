#!/usr/bin/env python3
"""
Comprehensive test script to verify peak/trough/mid-cycle detection
for multiple instruments and all their cycles.
"""

import requests
import json
from typing import List, Dict, Tuple
import numpy as np

BASE_URL = "http://localhost:5001"

def find_peaks(signal: List[float], wavelength: int, min_distance: int = None) -> List[int]:
    """Python implementation of frontend findPeaks function"""
    distance = min_distance or wavelength // 4

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

        # Keep highest in window
        best = max(window, key=lambda p: p['value'])
        filtered_peaks.append(best['idx'])
        i = j

    return filtered_peaks

def find_troughs(signal: List[float], wavelength: int, min_distance: int = None) -> List[int]:
    """Python implementation of frontend findTroughs function"""
    distance = min_distance or wavelength // 4

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

        # Keep lowest in window
        best = min(window, key=lambda p: p['value'])
        filtered_troughs.append(best['idx'])
        i = j

    return filtered_troughs

def find_mid_cycles(signal: List[float]) -> List[int]:
    """Find zero crossings (mid-cycle points)"""
    mid_cycles = []
    for i in range(1, len(signal)):
        prev = signal[i-1]
        curr = signal[i]
        if (prev < 0 and curr >= 0) or (prev > 0 and curr <= 0):
            mid_cycles.append(i)
    return mid_cycles

def apply_phase_shift(values: List[float], shift: int) -> List[float]:
    """Apply phase shift to signal"""
    if shift == 0:
        return values
    return values[shift:] + values[:shift]

def scale_bandpass(bandpass: List[float]) -> List[float]:
    """Center and scale bandpass like frontend does"""
    mean = sum(bandpass) / len(bandpass)
    centered = [v - mean for v in bandpass]
    scale_factor = 0.8
    scaled = [v * scale_factor for v in centered]
    return scaled

def test_cycle(symbol: str, wavelength: int, window_size: int = 4000) -> Dict:
    """Test a single cycle for a symbol"""
    print(f"\n  Testing {symbol} - {wavelength}d cycle...")

    url = f"{BASE_URL}/api/bandpass?symbol={symbol}&selected_wavelength={wavelength}&window_size={window_size}"
    response = requests.get(url)

    if response.status_code != 200:
        return {'error': f'HTTP {response.status_code}'}

    data = response.json()
    bandpass_data = data['bandpass']

    # Get raw bandpass values
    raw_bandpass = bandpass_data['scaled_values']

    # Simulate frontend processing with default phase shift (0)
    phase_shift = 0
    shifted_bandpass = apply_phase_shift(raw_bandpass, phase_shift)
    scaled_bandpass = scale_bandpass(shifted_bandpass)

    # Detect peaks, troughs, mid-cycles
    wavelength_val = bandpass_data['wavelength']
    peaks = find_peaks(scaled_bandpass, wavelength_val)
    troughs = find_troughs(scaled_bandpass, wavelength_val)
    mid_cycles = find_mid_cycles(scaled_bandpass)

    dates = data['price_data']['dates']

    result = {
        'wavelength': wavelength,
        'data_length': len(dates),
        'bandpass_length': len(raw_bandpass),
        'backend_peaks': len(bandpass_data['peaks']),
        'backend_troughs': len(bandpass_data['troughs']),
        'frontend_peaks': len(peaks),
        'frontend_troughs': len(troughs),
        'mid_cycles': len(mid_cycles),
        'peak_dates': [dates[i] for i in peaks[:3]] if len(peaks) >= 3 else [dates[i] for i in peaks],
        'trough_dates': [dates[i] for i in troughs[:3]] if len(troughs) >= 3 else [dates[i] for i in troughs],
    }

    # Validation
    issues = []

    if len(peaks) == 0:
        issues.append("❌ NO PEAKS DETECTED")
    if len(troughs) == 0:
        issues.append("❌ NO TROUGHS DETECTED")
    if len(mid_cycles) == 0:
        issues.append("❌ NO MID-CYCLES DETECTED")

    # Peaks and troughs should be roughly equal (within 1-2)
    if abs(len(peaks) - len(troughs)) > 2:
        issues.append(f"⚠️  Peak/trough mismatch: {len(peaks)} peaks vs {len(troughs)} troughs")

    # Should have reasonable number of cycles
    expected_cycles = len(dates) / wavelength_val
    actual_cycles = len(peaks)
    if actual_cycles < expected_cycles * 0.3:
        issues.append(f"⚠️  Too few peaks: expected ~{expected_cycles:.1f}, got {actual_cycles}")

    result['issues'] = issues
    result['status'] = '✅ PASS' if len(issues) == 0 else '❌ FAIL'

    return result

def test_symbol(symbol: str, window_size: int = 4000) -> Dict:
    """Test all cycles for a symbol"""
    print(f"\n{'='*60}")
    print(f"Testing {symbol}")
    print(f"{'='*60}")

    # Get initial analysis to find all cycles
    url = f"{BASE_URL}/api/analyze?symbol={symbol}&window_size={window_size}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"❌ Failed to analyze {symbol}: HTTP {response.status_code}")
        return {'error': f'HTTP {response.status_code}'}

    data = response.json()
    cycles = data.get('peak_cycles', [])

    if not cycles:
        print(f"❌ No cycles found for {symbol}")
        return {'error': 'No cycles found'}

    print(f"\nFound {len(cycles)} cycles: {[c['wavelength_days'] for c in cycles]}")

    results = []
    all_passed = True

    for cycle in cycles:
        wavelength = cycle['wavelength_days']
        result = test_cycle(symbol, wavelength, window_size)
        results.append(result)

        # Print summary
        print(f"\n    Wavelength: {result['wavelength']}d")
        print(f"    Data length: {result['data_length']}")
        print(f"    Frontend peaks: {result['frontend_peaks']} | troughs: {result['frontend_troughs']} | mid-cycles: {result['mid_cycles']}")

        if result['peak_dates']:
            print(f"    First 3 peak dates: {', '.join(result['peak_dates'])}")

        if result['issues']:
            print(f"    {result['status']}")
            for issue in result['issues']:
                print(f"      {issue}")
            all_passed = False
        else:
            print(f"    {result['status']}")

    return {
        'symbol': symbol,
        'cycles_tested': len(results),
        'results': results,
        'all_passed': all_passed
    }

def main():
    print("="*60)
    print("COMPREHENSIVE CYCLE LABEL DETECTION TEST")
    print("="*60)
    print("\nTesting multiple instruments with all their cycles...")
    print("This verifies that peak/trough/mid-cycle detection works correctly")
    print("using the unified frontend approach for ALL wavelengths.")

    # Test symbols with different characteristics
    test_symbols = [
        ('IWM', 4000),   # Small caps - typically has multiple cycles
        ('HON', 4000),   # Industrial - reported issues with 430d/500d
        ('AAPL', 4000),  # Tech - high volatility
        ('SPY', 4000),   # S&P 500 - benchmark
        ('TLT', 4000),   # Bonds - different behavior from stocks
    ]

    all_results = []
    total_passed = 0
    total_failed = 0

    for symbol, window_size in test_symbols:
        result = test_symbol(symbol, window_size)
        all_results.append(result)

        if result.get('all_passed'):
            total_passed += 1
        else:
            total_failed += 1

    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")

    for result in all_results:
        if 'error' in result:
            print(f"\n{result.get('symbol', 'Unknown')}: ❌ ERROR - {result['error']}")
        else:
            status = "✅ ALL PASSED" if result['all_passed'] else "❌ SOME FAILED"
            print(f"\n{result['symbol']}: {status} ({result['cycles_tested']} cycles tested)")

            for cycle_result in result['results']:
                cycle_status = cycle_result['status']
                issues_summary = f" - {len(cycle_result['issues'])} issues" if cycle_result['issues'] else ""
                print(f"  {cycle_result['wavelength']}d: {cycle_status}{issues_summary}")

    print(f"\n{'='*60}")
    print(f"Total Symbols Tested: {len(all_results)}")
    print(f"Passed: {total_passed} | Failed: {total_failed}")
    print(f"{'='*60}")

    if total_failed == 0:
        print("\n✅ ALL TESTS PASSED - Label detection works correctly for all cycles!")
        return 0
    else:
        print(f"\n❌ {total_failed} symbol(s) failed - review issues above")
        return 1

if __name__ == '__main__':
    exit(main())
