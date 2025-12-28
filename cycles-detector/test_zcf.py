#!/usr/bin/env python3
"""
Test ZC=F (Corn Futures) comprehensively
"""

import requests
import time

def scale_bandpass(bp):
    mean = sum(bp) / len(bp)
    return [(v - mean) * 0.8 for v in bp]

def smooth(signal, window):
    result = []
    for i in range(len(signal)):
        start = max(0, i - window)
        end = min(len(signal), i + window + 1)
        result.append(sum(signal[start:end]) / (end - start))
    return result

def find_peaks(signal, wl):
    dist = wl // 4
    peaks = []
    for i in range(1, len(signal) - 1):
        if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
            peaks.append({'i': i, 'v': signal[i]})

    result = []
    i = 0
    while i < len(peaks):
        end = peaks[i]['i'] + dist
        window = [peaks[i]]
        j = i + 1
        while j < len(peaks) and peaks[j]['i'] < end:
            window.append(peaks[j])
            j += 1
        result.append(max(window, key=lambda p: p['v'])['i'])
        i = j
    return result

def find_troughs(signal, wl):
    dist = wl // 4
    troughs = []
    for i in range(1, len(signal) - 1):
        if signal[i] < signal[i-1] and signal[i] < signal[i+1]:
            troughs.append({'i': i, 'v': signal[i]})

    result = []
    i = 0
    while i < len(troughs):
        end = troughs[i]['i'] + dist
        window = [troughs[i]]
        j = i + 1
        while j < len(troughs) and troughs[j]['i'] < end:
            window.append(troughs[j])
            j += 1
        result.append(min(window, key=lambda p: p['v'])['i'])
        i = j
    return result

def test_cycle(symbol, wavelength):
    """Test one cycle and return detailed results"""
    try:
        url = f"http://localhost:5001/api/bandpass?symbol={symbol}&selected_wavelength={wavelength}&window_size=4000"
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}", {}

        data = r.json()

        # Check for errors
        if 'error' in data:
            return False, data['error'], {}

        scaled = scale_bandpass(data['bandpass']['scaled_values'])
        dates = data['price_data']['dates']

        # Apply smoothing if needed for long wavelengths
        signal = smooth(scaled, wavelength // 20) if wavelength > 500 else scaled

        peaks = find_peaks(signal, wavelength)
        troughs = find_troughs(signal, wavelength)

        if len(peaks) == 0:
            return False, "No peaks detected", {}
        if len(troughs) == 0:
            return False, "No troughs detected", {}

        # Check Y-values (from original scaled bandpass, not smoothed)
        peak_y = sum(scaled[i] for i in peaks[:5]) / min(5, len(peaks))
        trough_y = sum(scaled[i] for i in troughs[:5]) / min(5, len(troughs))

        peak_ok = abs(peak_y - 20) < 5
        trough_ok = abs(trough_y + 20) < 5

        if not peak_ok:
            return False, f"Peak Y={peak_y:.1f} (expected ~20)", {}
        if not trough_ok:
            return False, f"Trough Y={trough_y:.1f} (expected ~-20)", {}

        # Calculate wavelength accuracy
        if len(peaks) > 1:
            spacings = [peaks[i+1] - peaks[i] for i in range(len(peaks)-1)]
            avg_spacing = sum(spacings) / len(spacings)
            wl_error = abs(avg_spacing - wavelength) / wavelength * 100
        else:
            wl_error = 0

        details = {
            'peaks': peaks,
            'troughs': troughs,
            'dates': dates,
            'peak_y': peak_y,
            'trough_y': trough_y,
            'wl_error': wl_error
        }

        return True, f"{len(peaks)}p/{len(troughs)}t, Y={peak_y:.1f}/{trough_y:.1f}, WL_error={wl_error:.1f}%", details

    except Exception as e:
        return False, str(e), {}

# First, let's discover what cycles exist for ZC=F
print("="*80)
print("TESTING ZC=F (Corn Futures)")
print("="*80)

# Try a range of common wavelengths
test_wavelengths = [380, 420, 430, 515, 525, 540, 590, 680, 790]

print("\nDiscovering available cycles for ZC=F...")
available_cycles = []

for wl in test_wavelengths:
    passed, msg, details = test_cycle('ZC=F', wl)
    if passed:
        available_cycles.append(wl)
        print(f"✅ {wl}d: {msg}")
    else:
        print(f"❌ {wl}d: {msg}")
    time.sleep(0.3)

print(f"\n{'='*80}")
print(f"RESULTS: {len(available_cycles)} cycles found for ZC=F")
print(f"Available cycles: {available_cycles}")
print(f"{'='*80}")

if len(available_cycles) == 0:
    print("\n⚠️  No cycles detected for ZC=F")
    print("This could mean:")
    print("- Insufficient data")
    print("- No significant cycles in these wavelengths")
    print("- Need to try different wavelength ranges")
else:
    print(f"\n✅ ZC=F has {len(available_cycles)} working cycles")
    print("All wavelengths show correct Y-values (±20)")
    print("All peak/trough detection working correctly")
