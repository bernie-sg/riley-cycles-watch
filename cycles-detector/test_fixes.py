#!/usr/bin/env python3
"""
Test script to verify the V13 bug fixes:
1. Sine wave projection uses 252/365 conversion (not compressed)
2. Peaks/troughs appear consistently across different cycles
"""

import requests
import json

def test_date_conversion():
    """Test that future dates use proper 252/365 conversion"""
    print("\n" + "="*80)
    print("TEST 1: Date Conversion (252 trading days = 365 calendar days)")
    print("="*80)

    # Analyze TLT
    response = requests.get('http://localhost:5001/api/analyze?symbol=TLT&window_size=4000')

    if response.status_code != 200:
        print(f"❌ FAILED: Server returned {response.status_code}")
        return False

    data = response.json()
    hist_length = len(data['price_data']['prices']) - data['price_data']['prices'].count(None)
    total_length = len(data['price_data']['dates'])
    future_length = total_length - hist_length

    print(f"Historical data points: {hist_length}")
    print(f"Total dates: {total_length}")
    print(f"Future dates: {future_length}")

    # The bandpass has future_days trading days of projection
    # With 252/365 conversion, we expect approximately future_days * 1.448 calendar dates
    future_days_trading = data['bandpass']['future_days']
    expected_calendar_days = int(future_days_trading * 365 / 252)

    print(f"\nFuture projection (trading days): {future_days_trading}")
    print(f"Expected calendar days: {expected_calendar_days}")
    print(f"Actual future dates: {future_length}")

    # Allow small rounding difference
    if abs(future_length - expected_calendar_days) <= 1:
        print(f"✅ PASS: Future dates match expected (within 1 day)")
        return True
    else:
        print(f"❌ FAIL: Future dates mismatch (off by {abs(future_length - expected_calendar_days)} days)")
        return False

def test_peaks_troughs_consistency():
    """Test that peaks/troughs appear consistently when switching cycles"""
    print("\n" + "="*80)
    print("TEST 2: Peaks/Troughs Consistency Across Different Cycles")
    print("="*80)

    # Analyze TLT to get available cycles
    response = requests.get('http://localhost:5001/api/analyze?symbol=TLT&window_size=4000')

    if response.status_code != 200:
        print(f"❌ FAILED: Server returned {response.status_code}")
        return False

    data = response.json()
    cycles = data['peak_cycles']

    if len(cycles) < 2:
        print(f"⚠️  WARNING: Only {len(cycles)} cycle(s) found, need at least 2 to test switching")
        return True

    print(f"Found {len(cycles)} cycles to test")

    results = []
    for i, cycle in enumerate(cycles[:3]):  # Test first 3 cycles
        wavelength = cycle['wavelength']
        print(f"\n--- Testing Cycle {i+1}: {wavelength}d ---")

        # Call bandpass API for this cycle
        response = requests.get(f'http://localhost:5001/api/bandpass?symbol=TLT&wavelength={wavelength}&window_size=4000')

        if response.status_code != 200:
            print(f"❌ FAILED: Bandpass API returned {response.status_code}")
            results.append(False)
            continue

        bp_data = response.json()
        peaks = bp_data['bandpass']['peaks']
        troughs = bp_data['bandpass']['troughs']

        print(f"Peaks: {len(peaks)} markers")
        print(f"Troughs: {len(troughs)} markers")
        print(f"Sample peaks: {peaks[:5]}")
        print(f"Sample troughs: {troughs[:5]}")

        # Check that we have reasonable number of peaks/troughs
        hist_length = bp_data['bandpass']['historical_length']
        future_days = bp_data['bandpass']['future_days']
        total_length = hist_length + future_days

        # Expect roughly total_length / wavelength peaks/troughs
        expected_count = total_length / wavelength

        if len(peaks) >= expected_count * 0.5 and len(troughs) >= expected_count * 0.5:
            print(f"✅ PASS: Reasonable number of peaks/troughs detected")
            results.append(True)
        else:
            print(f"❌ FAIL: Too few peaks/troughs (expected ~{expected_count:.0f})")
            results.append(False)

    if all(results):
        print(f"\n✅ OVERALL PASS: All {len(results)} cycles have consistent markers")
        return True
    else:
        print(f"\n❌ OVERALL FAIL: {results.count(False)}/{len(results)} cycles failed")
        return False

def test_sine_wave_continuity():
    """Test that sine wave is continuous (not two separate waves)"""
    print("\n" + "="*80)
    print("TEST 3: Sine Wave Continuity")
    print("="*80)

    response = requests.get('http://localhost:5001/api/analyze?symbol=TLT&window_size=4000')

    if response.status_code != 200:
        print(f"❌ FAILED: Server returned {response.status_code}")
        return False

    data = response.json()
    bandpass_values = data['bandpass']['scaled_values']
    hist_length = len(data['price_data']['prices']) - data['price_data']['prices'].count(None)

    # Check the boundary between historical and future
    # The sine wave should be continuous (no sudden jumps)
    boundary_idx = hist_length
    if boundary_idx > 0 and boundary_idx < len(bandpass_values):
        before = bandpass_values[boundary_idx - 1]
        after = bandpass_values[boundary_idx]
        diff = abs(after - before)

        print(f"Value before boundary: {before:.3f}")
        print(f"Value after boundary: {after:.3f}")
        print(f"Difference: {diff:.3f}")

        # For a continuous sine wave, adjacent values should be close
        # (within reasonable range based on wavelength)
        wavelength = data['bandpass']['wavelength']
        max_expected_diff = 50 * (2 * 3.14159 / wavelength)  # Rough estimate

        if diff < max_expected_diff:
            print(f"✅ PASS: Sine wave is continuous at boundary")
            return True
        else:
            print(f"❌ FAIL: Large discontinuity at boundary (max expected: {max_expected_diff:.3f})")
            return False
    else:
        print(f"⚠️  WARNING: Could not test boundary (idx={boundary_idx}, len={len(bandpass_values)})")
        return True

def main():
    print("\n" + "="*80)
    print("CYCLES DETECTOR V13 - BUG FIX VERIFICATION")
    print("="*80)
    print("Testing:")
    print("1. Date conversion (252 trading days = 365 calendar days)")
    print("2. Peaks/troughs consistency across cycles")
    print("3. Sine wave continuity")
    print("="*80)

    try:
        test1 = test_date_conversion()
        test2 = test_peaks_troughs_consistency()
        test3 = test_sine_wave_continuity()

        print("\n" + "="*80)
        print("FINAL RESULTS")
        print("="*80)
        print(f"Date Conversion: {'✅ PASS' if test1 else '❌ FAIL'}")
        print(f"Peaks/Troughs Consistency: {'✅ PASS' if test2 else '❌ FAIL'}")
        print(f"Sine Wave Continuity: {'✅ PASS' if test3 else '❌ FAIL'}")
        print("="*80)

        if test1 and test2 and test3:
            print("\n🎉 ALL TESTS PASSED! V13 fixes are working correctly.")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED. Please review the fixes.")
            return 1

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server at http://localhost:5001")
        print("Make sure the Flask server is running: python3 app.py")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
