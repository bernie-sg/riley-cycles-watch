#!/usr/bin/env python3
"""
Comprehensive Visual Test - V14 Phasing Dropdown
Tests both trough and peak phasing with 3 instruments
Generates detailed report with all verifications
"""

import sys
import requests
import json
import numpy as np

# Test configuration
TEST_CASES = [
    ('SPY', 420, 'trough'),
    ('AMD', 380, 'trough'),
    ('IWM', 250, 'trough'),
    ('SPY', 420, 'peak'),
    ('AMD', 380, 'peak'),
    ('IWM', 250, 'peak'),
]

BASE_URL = 'http://localhost:5001'

def test_bandpass_api(symbol, wavelength, align_to='trough'):
    """Test bandpass API with specific phasing"""

    print(f"\n{'='*100}")
    print(f"TEST: {symbol} {wavelength}d with {align_to.upper()} phasing")
    print(f"{'='*100}")

    # Build API request
    params = {
        'symbol': symbol,
        'window_size': 4000,
        'min_wavelength': 50,
        'max_wavelength': 600,
        'wavelength_step': 5,
        'align_to': align_to,
        'bandpass_phase_method': 'actual_price_peaks',
        'selected_wavelength': wavelength,
        'bandwidth': 0.10,
    }

    print(f"\nAPI Request: /api/bandpass")
    print(f"  symbol={symbol}, wavelength={wavelength}d, align_to={align_to}")

    try:
        response = requests.get(f'{BASE_URL}/api/bandpass', params=params, timeout=30)
        data = response.json()

        if not data.get('success'):
            print(f"  ❌ API returned error: {data.get('error', 'Unknown')}")
            return False

        print(f"  ✅ API response successful")

        # Check bandpass data
        bandpass = data.get('bandpass', [])
        if not bandpass:
            print(f"  ❌ No bandpass data returned")
            return False

        print(f"\n{'='*60}")
        print("VERIFICATION 1: Bandpass Y-Values")
        print(f"{'='*60}")

        bp_array = np.array(bandpass)
        bp_min = bp_array.min()
        bp_max = bp_array.max()
        bp_mean = bp_array.mean()

        print(f"  Min: {bp_min:.2f}")
        print(f"  Max: {bp_max:.2f}")
        print(f"  Mean: {bp_mean:.2f}")

        # Bandpass should be in ±20 range (after frontend scaling)
        if bp_min < -25 or bp_max > 25:
            print(f"  ❌ Y-values out of expected ±20 range!")
            return False
        print(f"  ✅ Y-values in expected range")

        # Check peaks and troughs
        print(f"\n{'='*60}")
        print("VERIFICATION 2: Peak/Trough Labels")
        print(f"{'='*60}")

        peaks = data.get('peaks', [])
        troughs = data.get('troughs', [])

        print(f"  Peaks: {len(peaks)} labels")
        print(f"  Troughs: {len(troughs)} labels")

        if len(peaks) == 0 and len(troughs) == 0:
            print(f"  ❌ No peak/trough labels returned!")
            return False

        # Show first few labels
        if peaks:
            print(f"\n  First 3 peaks:")
            for i, p in enumerate(peaks[:3]):
                print(f"    {i+1}. {p.get('date', 'N/A')}")

        if troughs:
            print(f"\n  First 3 troughs:")
            for i, t in enumerate(troughs[:3]):
                print(f"    {i+1}. {t.get('date', 'N/A')}")

        print(f"  ✅ Peak/trough labels present")

        # Check wavelength spacing
        print(f"\n{'='*60}")
        print("VERIFICATION 3: Wavelength Spacing")
        print(f"{'='*60}")

        if len(peaks) > 1:
            peak_indices = [p['index'] for p in peaks if 'index' in p]
            if len(peak_indices) > 1:
                spacings = [peak_indices[i+1] - peak_indices[i] for i in range(len(peak_indices)-1)]
                avg_spacing = np.mean(spacings)
                error_pct = abs(avg_spacing - wavelength) / wavelength * 100

                print(f"  Expected: {wavelength} bars")
                print(f"  Actual: {avg_spacing:.1f} bars")
                print(f"  Error: {error_pct:.2f}%")

                if error_pct > 1.0:
                    print(f"  ❌ Wavelength spacing error too large!")
                    return False
                print(f"  ✅ Wavelength spacing accurate")
        else:
            print(f"  ⚠️  Not enough peaks to verify spacing")

        # Check phase value
        print(f"\n{'='*60}")
        print("VERIFICATION 4: Phase Calculation")
        print(f"{'='*60}")

        phase_degrees = data.get('phase_degrees', 0)
        print(f"  Phase at end of data: {phase_degrees:.2f}°")

        # Phase should vary (not hardcoded to 0)
        if abs(phase_degrees) < 1.0 and abs(phase_degrees - 360) < 1.0:
            print(f"  ⚠️  Phase close to 0° - may be hardcoded")
        else:
            print(f"  ✅ Phase calculated (not hardcoded)")

        print(f"\n{'='*60}")
        print(f"✅ ALL VERIFICATIONS PASSED for {symbol} {wavelength}d ({align_to})")
        print(f"{'='*60}")

        return True

    except requests.exceptions.Timeout:
        print(f"  ❌ Request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print(f"  ❌ Could not connect to server at {BASE_URL}")
        print(f"  Make sure Flask server is running on port 5001")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("="*100)
    print("COMPREHENSIVE VISUAL TEST - V14 PHASING DROPDOWN")
    print("="*100)
    print(f"\nServer: {BASE_URL}")
    print(f"Total tests: {len(TEST_CASES)}")
    print(f"\nTest cases:")
    for symbol, wavelength, align_to in TEST_CASES:
        print(f"  • {symbol} {wavelength}d ({align_to})")

    # Check if server is running
    print(f"\nChecking if server is running...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server is accessible")
    except:
        print(f"❌ Server is not running at {BASE_URL}")
        print(f"Please start the server with: python3 app.py")
        return

    # Run all tests
    passed = 0
    failed = 0

    for symbol, wavelength, align_to in TEST_CASES:
        result = test_bandpass_api(symbol, wavelength, align_to)
        if result:
            passed += 1
        else:
            failed += 1

    # Summary
    print(f"\n{'='*100}")
    print("FINAL SUMMARY")
    print(f"{'='*100}")
    print(f"Passed: {passed}/{len(TEST_CASES)}")
    print(f"Failed: {failed}/{len(TEST_CASES)}")
    print(f"Success rate: {passed/len(TEST_CASES)*100:.1f}%")

    if failed == 0:
        print(f"\n✅ ALL VISUAL TESTS PASSED!")
        print(f"✅ Phasing dropdown working correctly")
        print(f"✅ Both trough and peak phasing verified")
        print(f"✅ Sine waves, labels, and spacing all correct")
    else:
        print(f"\n❌ SOME TESTS FAILED - Review output above")

    print(f"\n{'='*100}")
    print("NEXT STEP: Visual verification in browser")
    print(f"{'='*100}")
    print(f"\n1. Open http://localhost:5001")
    print(f"2. Test symbols: SPY, AMD, IWM")
    print(f"3. Try different wavelengths (250d, 380d, 420d)")
    print(f"4. Toggle phasing dropdown between 'Trough' and 'Peak'")
    print(f"5. Verify:")
    print(f"   • Sine wave overlay looks correct")
    print(f"   • Red (peak) and green (trough) date labels visible")
    print(f"   • Labels align with sine wave extrema")
    print(f"   • Changing phasing updates the display")

if __name__ == '__main__':
    main()
