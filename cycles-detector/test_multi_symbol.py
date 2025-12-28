#!/usr/bin/env python3
"""
Test that V13 fixes work consistently across multiple symbols
"""

import requests

def test_symbol(symbol):
    """Test a single symbol"""
    print(f"\n{'='*80}")
    print(f"Testing {symbol}")
    print('='*80)

    # Analyze symbol
    response = requests.get(f'http://localhost:5001/api/analyze?symbol={symbol}&window_size=4000')

    if response.status_code != 200:
        print(f"❌ FAILED: Server returned {response.status_code}")
        return False

    data = response.json()

    # Check date conversion
    hist_length = len(data['price_data']['prices']) - data['price_data']['prices'].count(None)
    total_length = len(data['price_data']['dates'])
    future_length = total_length - hist_length
    future_days_trading = data['bandpass']['future_days']
    expected_calendar_days = int(future_days_trading * 365 / 252)

    print(f"Historical: {hist_length} bars")
    print(f"Future (trading days): {future_days_trading}")
    print(f"Future (calendar days): {future_length} (expected {expected_calendar_days})")

    date_ok = abs(future_length - expected_calendar_days) <= 1
    print(f"Date conversion: {'✅' if date_ok else '❌'}")

    # Check sine wave continuity
    bandpass = data['bandpass']['scaled_values']
    boundary = hist_length
    if boundary > 0 and boundary < len(bandpass):
        before = bandpass[boundary - 1]
        after = bandpass[boundary]
        diff = abs(after - before)
        wave_ok = diff < 10  # Should be smooth transition
        print(f"Sine wave continuity: {'✅' if wave_ok else '❌'} (diff={diff:.2f})")
    else:
        wave_ok = True
        print(f"Sine wave continuity: ⚠️  (couldn't test)")

    # Check cycles
    cycles = data['peak_cycles']
    cycles_ok = len(cycles) > 0
    print(f"Cycles detected: {len(cycles)} {'✅' if cycles_ok else '❌'}")

    # Test switching between cycles
    if len(cycles) >= 2:
        print(f"\nTesting cycle switching...")
        switch_ok = True
        for i, cycle in enumerate(cycles[:2]):
            wavelength = cycle['wavelength']
            response = requests.get(f'http://localhost:5001/api/bandpass?symbol={symbol}&wavelength={wavelength}&window_size=4000')
            if response.status_code == 200:
                bp_data = response.json()
                peaks = len(bp_data['bandpass']['peaks'])
                troughs = len(bp_data['bandpass']['troughs'])
                print(f"  Cycle {wavelength}d: {peaks} peaks, {troughs} troughs ✅")
            else:
                print(f"  Cycle {wavelength}d: ❌ Failed")
                switch_ok = False
        print(f"Cycle switching: {'✅' if switch_ok else '❌'}")
    else:
        switch_ok = True
        print(f"Cycle switching: ⚠️  (only {len(cycles)} cycle(s), need 2+)")

    all_ok = date_ok and wave_ok and cycles_ok and switch_ok
    print(f"\n{symbol} Overall: {'✅ PASS' if all_ok else '❌ FAIL'}")
    return all_ok

def main():
    print("\n" + "="*80)
    print("MULTI-SYMBOL CONSISTENCY TEST")
    print("="*80)
    print("Testing V13 fixes across different instruments")
    print("="*80)

    symbols = ['TLT', 'IWM', 'QQQ', 'NFLX']
    results = {}

    try:
        for symbol in symbols:
            results[symbol] = test_symbol(symbol)

        print("\n" + "="*80)
        print("FINAL RESULTS")
        print("="*80)
        for symbol, result in results.items():
            print(f"{symbol}: {'✅ PASS' if result else '❌ FAIL'}")
        print("="*80)

        if all(results.values()):
            print("\n🎉 ALL SYMBOLS PASSED! Fixes work consistently across instruments.")
            return 0
        else:
            print(f"\n❌ {sum(not r for r in results.values())}/{len(results)} symbols failed")
            return 1

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
