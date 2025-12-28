#!/usr/bin/env python3
"""
Comprehensive Test Script for Wavelength Bug Fix
Tests all instruments and their cycles to verify wavelengths are correct
"""

import sys
import os
import numpy as np
from scipy.signal import find_peaks

# Add algorithms to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'algorithms'))
sys.path.append('algorithms/bandpass')

from algorithms.bandpass.pure_sine_bandpass import create_pure_sine_bandpass
from data_manager import DataManager

# Define instruments and their key cycles (in TRADING DAYS)
INSTRUMENTS = {
    'AMD': [380, 420, 515, 590],
    'AAPL': [380, 420, 515],
    'MSFT': [380, 420, 515],
    'GOOGL': [380, 420, 515],
    'NVDA': [380, 420, 515, 590],
    'SPY': [380, 420, 515],
    'QQQ': [380, 420, 515],
    'IWM': [380, 420, 515],
    'TLT': [380, 420, 515, 590],
    'GLD': [380, 420, 515]
}

def measure_peak_spacing(sine_wave, expected_wavelength):
    """
    Measure actual peak spacing in sine wave
    Returns average spacing and all individual spacings
    """
    # Find peaks with reasonable distance
    peaks, _ = find_peaks(sine_wave, distance=int(expected_wavelength * 0.4))

    if len(peaks) < 2:
        return None, []

    # Calculate spacings between consecutive peaks
    spacings = np.diff(peaks)
    avg_spacing = np.mean(spacings)

    return avg_spacing, spacings.tolist()

def verify_peak_values(sine_wave, peaks, tolerance=0.1):
    """
    Verify that peaks have Y-values near +1.0 (normalized)
    tolerance: acceptable deviation from 1.0
    """
    if len(peaks) == 0:
        return False, []

    peak_values = [sine_wave[p] for p in peaks]
    valid = [abs(v - 1.0) < tolerance for v in peak_values]

    return all(valid), peak_values

def verify_trough_values(sine_wave, troughs, tolerance=0.1):
    """
    Verify that troughs have Y-values near -1.0 (normalized)
    """
    if len(troughs) == 0:
        return False, []

    trough_values = [sine_wave[t] for t in troughs]
    valid = [abs(v - (-1.0)) < tolerance for v in trough_values]

    return all(valid), trough_values

def test_wavelength(symbol, wavelength):
    """
    Test a single wavelength for a symbol
    Returns dict with test results
    """
    result = {
        'symbol': symbol,
        'wavelength': wavelength,
        'passed': False,
        'avg_spacing': None,
        'spacing_error_pct': None,
        'peak_spacings': [],
        'peak_values_valid': False,
        'trough_values_valid': False,
        'error': None
    }

    try:
        # Load data
        dm = DataManager(symbol)
        prices, price_df = dm.get_data()

        if len(prices) < wavelength * 3:
            result['error'] = f"Insufficient data: {len(prices)} bars"
            return result

        # Generate bandpass with zero future projection
        bp_result = create_pure_sine_bandpass(
            prices,
            wavelength,
            bandwidth_pct=0.10,
            extend_future=0,
            method='actual_price_peaks',
            align_to='trough'
        )

        sine_wave = bp_result['bandpass_normalized']

        # Measure peak spacing
        avg_spacing, spacings = measure_peak_spacing(sine_wave, wavelength)

        if avg_spacing is None:
            result['error'] = "Could not find peaks"
            return result

        result['avg_spacing'] = float(avg_spacing)
        result['peak_spacings'] = spacings

        # Calculate error percentage
        spacing_error_pct = abs(avg_spacing - wavelength) / wavelength * 100
        result['spacing_error_pct'] = float(spacing_error_pct)

        # Find peaks and troughs
        peaks, _ = find_peaks(sine_wave, distance=int(wavelength * 0.4))
        troughs, _ = find_peaks(-sine_wave, distance=int(wavelength * 0.4))

        # Verify peak values
        peak_valid, peak_values = verify_peak_values(sine_wave, peaks, tolerance=0.15)
        result['peak_values_valid'] = peak_valid
        result['peak_values'] = [float(v) for v in peak_values[:5]]  # First 5

        # Verify trough values
        trough_valid, trough_values = verify_trough_values(sine_wave, troughs, tolerance=0.15)
        result['trough_values_valid'] = trough_valid
        result['trough_values'] = [float(v) for v in trough_values[:5]]  # First 5

        # Test passes if:
        # 1. Spacing error < 15% (allows for some variance)
        # 2. Peak values are valid
        # 3. Trough values are valid
        result['passed'] = (
            spacing_error_pct < 15.0 and
            peak_valid and
            trough_valid
        )

    except Exception as e:
        result['error'] = str(e)

    return result

def main():
    """
    Run comprehensive tests on all instruments and cycles
    """
    print("=" * 80)
    print("WAVELENGTH BUG FIX - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()
    print("Testing that sine waves have CORRECT wavelengths (no 1.451 conversion)")
    print("Expected: User requests 420d cycle → sine wave has 420-day peaks spacing")
    print("Tolerance: ±15% spacing error allowed")
    print()

    all_results = []
    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for symbol, wavelengths in INSTRUMENTS.items():
        print(f"\n{'=' * 80}")
        print(f"Testing {symbol} - {len(wavelengths)} cycles")
        print(f"{'=' * 80}")

        for wavelength in wavelengths:
            total_tests += 1
            print(f"\n  Testing {wavelength}d cycle...")

            result = test_wavelength(symbol, wavelength)
            all_results.append(result)

            if result['error']:
                print(f"    ERROR: {result['error']}")
                failed_tests += 1
                continue

            # Print results
            print(f"    Expected wavelength:  {wavelength}d")
            print(f"    Measured avg spacing: {result['avg_spacing']:.1f}d")
            print(f"    Spacing error:        {result['spacing_error_pct']:.2f}%")
            print(f"    Peak spacings:        {[f'{s:.0f}d' for s in result['peak_spacings'][:5]]}")
            print(f"    Peak values valid:    {result['peak_values_valid']} {result['peak_values'][:3]}")
            print(f"    Trough values valid:  {result['trough_values_valid']} {result['trough_values'][:3]}")

            if result['passed']:
                print(f"    ✓ PASSED")
                passed_tests += 1
            else:
                print(f"    ✗ FAILED")
                failed_tests += 1

                # Print failure details
                if result['spacing_error_pct'] >= 15.0:
                    print(f"      - Spacing error too high: {result['spacing_error_pct']:.2f}% (max 15%)")
                if not result['peak_values_valid']:
                    print(f"      - Peak values incorrect: {result['peak_values'][:3]}")
                if not result['trough_values_valid']:
                    print(f"      - Trough values incorrect: {result['trough_values'][:3]}")

    # Print summary
    print(f"\n{'=' * 80}")
    print("TEST SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total tests:  {total_tests}")
    print(f"Passed:       {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Failed:       {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    print()

    if failed_tests == 0:
        print("✓ ALL TESTS PASSED - Wavelength bug is FIXED!")
        print()
        return 0
    else:
        print("✗ SOME TESTS FAILED - Wavelength bug NOT fully fixed")
        print()
        print("Failed tests:")
        for result in all_results:
            if not result['passed'] and not result['error']:
                print(f"  - {result['symbol']} {result['wavelength']}d: "
                      f"spacing error {result['spacing_error_pct']:.2f}%")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
