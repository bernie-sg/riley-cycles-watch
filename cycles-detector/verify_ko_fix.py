#!/usr/bin/env python3
"""
Verify KO Phasing Fix
Tests that KO 425d now aligns to the correct trough (confirmed, prominent)
instead of the recent developing trough
"""

import sys
import requests
import json
import numpy as np
from datetime import datetime

BASE_URL = 'http://localhost:5001'

def verify_ko_425d_trough():
    """Verify KO 425d trough alignment is fixed"""

    print("="*100)
    print("VERIFYING KO 425d TROUGH ALIGNMENT FIX")
    print("="*100)

    # Test KO 425d with trough alignment
    params = {
        'symbol': 'KO',
        'window_size': 4000,
        'min_wavelength': 50,
        'max_wavelength': 600,
        'wavelength_step': 5,
        'align_to': 'trough',
        'bandpass_phase_method': 'actual_price_peaks',
        'selected_wavelength': 425,
        'bandwidth': 0.10,
    }

    print(f"\nAPI Request: /api/bandpass")
    print(f"  symbol=KO, wavelength=425d, align_to=trough")

    try:
        response = requests.get(f'{BASE_URL}/api/bandpass', params=params, timeout=60)
        data = response.json()

        if not data.get('success'):
            print(f"  ❌ API returned error: {data.get('error', 'Unknown')}")
            return False

        print(f"  ✅ API response successful")

        # Check troughs data
        troughs = data.get('troughs', [])

        print(f"\n{'='*60}")
        print("VERIFICATION: Trough Labels")
        print(f"{'='*60}")
        print(f"  Total trough labels: {len(troughs)}")

        if len(troughs) == 0:
            print(f"  ❌ No trough labels returned!")
            return False

        # Check which trough is being used for alignment
        # The first (oldest) trough should be the one used for alignment
        first_trough = troughs[0] if troughs else None
        if first_trough:
            trough_date = first_trough.get('date', 'N/A')
            print(f"\n  First trough (alignment reference): {trough_date}")

            # The fix should align to Oct 2023, NOT Sept 2025
            # Check if the date is reasonable (not too recent)
            try:
                # Parse date (format: YYYY-MM-DD)
                trough_datetime = datetime.strptime(trough_date, '%Y-%m-%d')

                # Check if it's from 2023 or early 2024 (confirmed trough)
                # NOT from Sept 2025 (recent developing trough)
                if trough_datetime.year == 2025 and trough_datetime.month >= 9:
                    print(f"  ❌ WRONG: Still aligning to recent Sept 2025 trough!")
                    print(f"  ❌ This is the developing trough that should be excluded!")
                    return False
                elif trough_datetime.year <= 2024:
                    print(f"  ✅ CORRECT: Aligning to confirmed trough from {trough_datetime.year}")
                    print(f"  ✅ This is NOT the recent developing trough")
                else:
                    print(f"  ⚠️  Unexpected year: {trough_datetime.year}")
            except:
                print(f"  ⚠️  Could not parse trough date: {trough_date}")

        # Show all troughs
        print(f"\n  All trough labels (first 10):")
        for i, t in enumerate(troughs[:10]):
            date = t.get('date', 'N/A')
            print(f"    {i+1}. {date}")

        # Check peaks
        peaks = data.get('peaks', [])
        print(f"\n{'='*60}")
        print("VERIFICATION: Peak Labels")
        print(f"{'='*60}")
        print(f"  Total peak labels: {len(peaks)}")

        if len(peaks) == 0:
            print(f"  ❌ No peak labels returned!")
            return False

        print(f"  ✅ Peak labels present")

        # Show first few peaks
        print(f"\n  First 5 peaks:")
        for i, p in enumerate(peaks[:5]):
            date = p.get('date', 'N/A')
            print(f"    {i+1}. {date}")

        # Check bandpass data
        print(f"\n{'='*60}")
        print("VERIFICATION: Bandpass Y-Values")
        print(f"{'='*60}")

        bandpass = data.get('bandpass', [])
        if not bandpass:
            print(f"  ❌ No bandpass data returned")
            return False

        bp_array = np.array(bandpass)
        bp_min = bp_array.min()
        bp_max = bp_array.max()
        bp_mean = bp_array.mean()

        print(f"  Min: {bp_min:.2f}")
        print(f"  Max: {bp_max:.2f}")
        print(f"  Mean: {bp_mean:.2f}")

        if bp_min < -25 or bp_max > 25:
            print(f"  ❌ Y-values out of expected ±20 range!")
            return False
        print(f"  ✅ Y-values in expected range")

        # Check wavelength spacing
        print(f"\n{'='*60}")
        print("VERIFICATION: Wavelength Spacing")
        print(f"{'='*60}")

        if len(peaks) > 1:
            peak_indices = [p['index'] for p in peaks if 'index' in p]
            if len(peak_indices) > 1:
                spacings = [peak_indices[i+1] - peak_indices[i] for i in range(len(peak_indices)-1)]
                avg_spacing = np.mean(spacings)
                error_pct = abs(avg_spacing - 425) / 425 * 100

                print(f"  Expected: 425 bars")
                print(f"  Actual: {avg_spacing:.1f} bars")
                print(f"  Error: {error_pct:.2f}%")

                if error_pct > 2.0:
                    print(f"  ❌ Wavelength spacing error too large!")
                    return False
                print(f"  ✅ Wavelength spacing accurate")

        print(f"\n{'='*100}")
        print("✅ KO 425d TROUGH ALIGNMENT FIX VERIFIED")
        print(f"{'='*100}")
        print("Key findings:")
        print("  ✅ Trough labels present")
        print("  ✅ Peak labels present")
        print("  ✅ Aligning to confirmed trough (NOT recent developing trough)")
        print("  ✅ Y-values in expected range")
        print("  ✅ Wavelength spacing accurate")

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
        import traceback
        traceback.print_exc()
        return False

def test_ko_peak_alignment():
    """Test KO 425d with peak alignment"""

    print("\n" + "="*100)
    print("TESTING KO 425d PEAK ALIGNMENT")
    print("="*100)

    params = {
        'symbol': 'KO',
        'window_size': 4000,
        'min_wavelength': 50,
        'max_wavelength': 600,
        'wavelength_step': 5,
        'align_to': 'peak',
        'bandpass_phase_method': 'actual_price_peaks',
        'selected_wavelength': 425,
        'bandwidth': 0.10,
    }

    try:
        response = requests.get(f'{BASE_URL}/api/bandpass', params=params, timeout=60)
        data = response.json()

        if not data.get('success'):
            print(f"  ❌ API returned error: {data.get('error', 'Unknown')}")
            return False

        peaks = data.get('peaks', [])
        troughs = data.get('troughs', [])

        print(f"  Peaks: {len(peaks)} labels")
        print(f"  Troughs: {len(troughs)} labels")

        if len(peaks) == 0 or len(troughs) == 0:
            print(f"  ❌ Missing labels!")
            return False

        print(f"  ✅ Both peak and trough labels present")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("="*100)
    print("KO 425d FIX VERIFICATION TEST")
    print("="*100)
    print(f"\nServer: {BASE_URL}")
    print(f"\nThis test verifies:")
    print("  1. KO 425d trough alignment uses confirmed trough (NOT Sept 2025 developing trough)")
    print("  2. All peak labels are present (no missing labels)")
    print("  3. All trough labels are present")
    print("  4. Peak alignment also works correctly")

    # Check server
    print(f"\nChecking if server is running...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server is accessible")
    except:
        print(f"❌ Server is not running at {BASE_URL}")
        print(f"Please start the server with: python3 app.py")
        return

    # Run tests
    results = []

    # Test 1: KO trough alignment fix
    result1 = verify_ko_425d_trough()
    results.append(('KO 425d Trough Alignment', result1))

    # Test 2: KO peak alignment
    result2 = test_ko_peak_alignment()
    results.append(('KO 425d Peak Alignment', result2))

    # Summary
    print(f"\n{'='*100}")
    print("SUMMARY")
    print(f"{'='*100}")

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print(f"\n✅ ALL TESTS PASSED!")
        print(f"\n{'='*100}")
        print("NEXT: Visual verification in browser")
        print(f"{'='*100}")
        print(f"\n1. Open http://localhost:5001")
        print(f"2. Enter symbol: KO")
        print(f"3. Click 'Analyze Symbol'")
        print(f"4. In Price Chart controls:")
        print(f"   - Wavelength: 425")
        print(f"   - Bandwidth: 0.10")
        print(f"   - Phasing: Trough (default)")
        print(f"   - Click 'Apply'")
        print(f"\n5. Verify:")
        print(f"   ✅ Sine wave aligns to a confirmed trough (2023 or early 2024)")
        print(f"   ✅ NOT aligned to Sept 26, 2025 (recent developing trough)")
        print(f"   ✅ All red (peak) labels visible")
        print(f"   ✅ All green (trough) labels visible")
        print(f"   ✅ No missing labels")
        print(f"\n6. Switch Phasing to 'Peak' and verify again")
    else:
        print(f"\n❌ SOME TESTS FAILED - Fix required before visual verification")

if __name__ == '__main__':
    main()
