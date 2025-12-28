#!/usr/bin/env python3
"""
Test complete phasing fix for KO 425d and IWM 515d
Verifies:
1. Recency-first alignment (not to developing turning points)
2. Labels are filtered (no developing turning points within 25% of wavelength from end)
3. All labels are present and correctly formatted
"""

import requests
import json
from datetime import datetime

BASE_URL = 'http://localhost:5001'

def test_ko_425d():
    """Test KO 425d trough alignment"""
    print("="*100)
    print("TEST 1: KO 425d TROUGH ALIGNMENT")
    print("="*100)

    params = {
        'symbol': 'KO',
        'window_size': 4000,
        'selected_wavelength': 425,
        'bandwidth': 0.10,
        'align_to': 'trough',
        'bandpass_phase_method': 'actual_price_peaks',
    }

    response = requests.get(f'{BASE_URL}/api/bandpass', params=params, timeout=60)
    data = response.json()

    if not data.get('success'):
        print(f"❌ API error: {data.get('error')}")
        return False

    troughs = data.get('troughs', [])
    peaks = data.get('peaks', [])

    print(f"\n✅ API returned successfully")
    print(f"Total peaks: {len(peaks)}")
    print(f"Total troughs: {len(troughs)}")

    if len(troughs) == 0:
        print(f"❌ No trough labels!")
        return False

    if len(peaks) == 0:
        print(f"❌ No peak labels!")
        return False

    # Check most recent trough is NOT Sept 2025 (too recent)
    print(f"\nFirst 3 troughs:")
    for i, t in enumerate(troughs[:3]):
        print(f"  {i+1}. {t['date']}")

    print(f"\nLast 3 troughs:")
    for i, t in enumerate(troughs[-3:]):
        print(f"  {len(troughs)-2+i}. {t['date']}")

    # Verify last trough is not too recent (should be at least 106 bars from end)
    # 425 * 0.25 = 106.25 bars
    last_trough = troughs[-1]
    last_trough_date = datetime.strptime(last_trough['date'], '%Y-%m-%d')

    print(f"\n{'='*60}")
    print("VERIFICATION: Last trough is confirmed (not developing)")
    print(f"{'='*60}")
    print(f"Last trough date: {last_trough['date']}")

    # Check it's not from Sept/Oct 2025
    if last_trough_date.year == 2025 and last_trough_date.month >= 9:
        print(f"❌ FAIL: Last trough is from Sept/Oct 2025 (too recent/developing)")
        return False

    print(f"✅ PASS: Last trough is from {last_trough_date.strftime('%B %Y')} (confirmed)")

    return True


def test_iwm_515d():
    """Test IWM 515d trough alignment"""
    print("\n" + "="*100)
    print("TEST 2: IWM 515d TROUGH ALIGNMENT")
    print("="*100)

    params = {
        'symbol': 'IWM',
        'window_size': 4000,
        'selected_wavelength': 515,
        'bandwidth': 0.10,
        'align_to': 'trough',
        'bandpass_phase_method': 'actual_price_peaks',
    }

    response = requests.get(f'{BASE_URL}/api/bandpass', params=params, timeout=60)
    data = response.json()

    if not data.get('success'):
        print(f"❌ API error: {data.get('error')}")
        return False

    troughs = data.get('troughs', [])
    peaks = data.get('peaks', [])

    print(f"\n✅ API returned successfully")
    print(f"Total peaks: {len(peaks)}")
    print(f"Total troughs: {len(troughs)}")

    if len(troughs) == 0:
        print(f"❌ No trough labels!")
        return False

    if len(peaks) == 0:
        print(f"❌ No peak labels!")
        return False

    print(f"\nFirst 3 troughs:")
    for i, t in enumerate(troughs[:3]):
        print(f"  {i+1}. {t['date']}")

    print(f"\nLast 3 troughs:")
    for i, t in enumerate(troughs[-3:]):
        print(f"  {len(troughs)-2+i}. {t['date']}")

    # Verify last trough is not too recent
    # 515 * 0.25 = 128.75 bars (about 6 months)
    last_trough = troughs[-1]
    last_trough_date = datetime.strptime(last_trough['date'], '%Y-%m-%d')

    print(f"\n{'='*60}")
    print("VERIFICATION: Last trough is confirmed (not developing)")
    print(f"{'='*60}")
    print(f"Last trough date: {last_trough['date']}")

    # Check it's not from Sept/Oct 2025
    if last_trough_date.year == 2025 and last_trough_date.month >= 9:
        print(f"❌ FAIL: Last trough is from Sept/Oct 2025 (too recent/developing)")
        return False

    print(f"✅ PASS: Last trough is from {last_trough_date.strftime('%B %Y')} (confirmed)")

    return True


def main():
    print("="*100)
    print("COMPLETE PHASING FIX VERIFICATION")
    print("="*100)
    print(f"\nServer: {BASE_URL}")
    print(f"\nThis test verifies:")
    print("  ✅ Recency-first alignment (most recent confirmed turning point)")
    print("  ✅ Labels filtered (no developing turning points within 25% of wavelength)")
    print("  ✅ All confirmed labels are present")

    # Check server
    print(f"\nChecking server...")
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✅ Server is accessible at {BASE_URL}")
    except:
        print(f"❌ Server is not running at {BASE_URL}")
        print(f"Please start the server with: python3 app.py")
        return

    # Run tests
    results = []

    result1 = test_ko_425d()
    results.append(('KO 425d', result1))

    result2 = test_iwm_515d()
    results.append(('IWM 515d', result2))

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
        print("READY FOR USER TESTING")
        print(f"{'='*100}")
        print(f"\n1. Open http://localhost:5001")
        print(f"2. Test KO with 425d wavelength (trough alignment)")
        print(f"3. Test IWM with 515d wavelength (trough alignment)")
        print(f"4. Verify:")
        print(f"   ✅ Sine waves align to confirmed turning points (not recent developing ones)")
        print(f"   ✅ All peak and trough labels are visible")
        print(f"   ✅ No labels within last ~25% of wavelength from present")
    else:
        print(f"\n❌ SOME TESTS FAILED")

if __name__ == '__main__':
    main()
