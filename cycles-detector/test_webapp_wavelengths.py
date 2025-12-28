#!/usr/bin/env python3
"""
Test the actual web application to verify wavelengths are correct
Tests the /api/bandpass endpoint for multiple instruments and cycles
"""

import requests
import json
import numpy as np
from scipy.signal import find_peaks

BASE_URL = "http://localhost:5001"

# Test cases: symbol, wavelength, expected_spacing_tolerance
TEST_CASES = [
    ('AMD', 380, 0.15),
    ('AMD', 420, 0.15),
    ('AMD', 515, 0.15),
    ('AMD', 590, 0.15),
    ('AAPL', 380, 0.15),
    ('AAPL', 420, 0.15),
    ('MSFT', 420, 0.15),
    ('NVDA', 420, 0.15),
    ('SPY', 420, 0.15),
    ('TLT', 420, 0.15),
]

def test_bandpass_endpoint(symbol, wavelength, tolerance=0.15):
    """
    Test a single bandpass endpoint call
    Verifies that the generated sine wave has correct wavelength
    """
    print(f"\nTesting {symbol} {wavelength}d cycle...")

    try:
        # Call API
        url = f"{BASE_URL}/api/bandpass"
        params = {
            'symbol': symbol,
            'selected_wavelength': wavelength,
            'bandwidth': 0.10,
            'bandpass_phase_method': 'actual_price_peaks',
            'align_to': 'trough'
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            print(f"  ERROR: HTTP {response.status_code}")
            return False

        data = response.json()

        if not data.get('success'):
            print(f"  ERROR: API returned success=false")
            return False

        # Get bandpass values
        bandpass_values = data['bandpass']['scaled_values']

        # Unscale (values are scaled to ±25 in API)
        bandpass_normalized = [v / 25.0 for v in bandpass_values]

        # Find peaks
        peaks, _ = find_peaks(bandpass_normalized, distance=int(wavelength * 0.4))

        if len(peaks) < 2:
            print(f"  ERROR: Not enough peaks found ({len(peaks)})")
            return False

        # Calculate average spacing
        spacings = np.diff(peaks)
        avg_spacing = np.mean(spacings)
        error_pct = abs(avg_spacing - wavelength) / wavelength

        print(f"  Expected:        {wavelength}d")
        print(f"  Measured:        {avg_spacing:.1f}d")
        print(f"  Error:           {error_pct*100:.2f}%")
        print(f"  Peak spacings:   {[f'{int(s)}d' for s in spacings[:5]]}")

        # Check peak values (should be ~1.0 when normalized)
        peak_values = [bandpass_normalized[p] for p in peaks[:5]]
        print(f"  Peak values:     {[f'{v:.3f}' for v in peak_values]}")

        # Test passes if error is within tolerance
        if error_pct <= tolerance:
            print(f"  ✓ PASSED")
            return True
        else:
            print(f"  ✗ FAILED - Error {error_pct*100:.2f}% exceeds {tolerance*100:.1f}%")
            return False

    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    print("=" * 80)
    print("WEB APPLICATION WAVELENGTH TEST")
    print("=" * 80)
    print(f"Testing {len(TEST_CASES)} cases via /api/bandpass endpoint")
    print()

    passed = 0
    failed = 0

    for symbol, wavelength, tolerance in TEST_CASES:
        if test_bandpass_endpoint(symbol, wavelength, tolerance):
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Total:  {len(TEST_CASES)}")
    print(f"Passed: {passed} ({passed/len(TEST_CASES)*100:.1f}%)")
    print(f"Failed: {failed}")
    print()

    if failed == 0:
        print("✓ ALL WEB APP TESTS PASSED - Wavelengths are correct!")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
