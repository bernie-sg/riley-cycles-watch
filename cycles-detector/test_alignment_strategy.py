#!/usr/bin/env python3
"""
Comprehensive test of alignment strategies:
1. Peak vs Trough alignment
2. Using 1, 3, 5, 7 most recent turning points
3. Measure how well sine wave aligns with actual price peaks/troughs
"""

import sys
import os
import numpy as np
from scipy.signal import find_peaks
import json

sys.path.insert(0, '/Users/bernie/Documents/Cycles Detector/Cycles Detector V14/webapp')

from data_manager import DataManager

def find_price_extrema(prices, wavelength):
    """Find actual price peaks and troughs"""
    # Detrend
    x = np.arange(len(prices))
    coeffs = np.polyfit(x, prices, 3)
    trend = np.polyval(coeffs, x)
    detrended = prices - trend

    min_distance = int(wavelength * 0.4)

    peaks_idx, _ = find_peaks(detrended, distance=min_distance, prominence=np.std(detrended) * 0.2)
    troughs_idx, _ = find_peaks(-detrended, distance=min_distance, prominence=np.std(detrended) * 0.2)

    return peaks_idx, troughs_idx, detrended

def generate_sine_wave_with_alignment(prices, wavelength, align_to, num_recent, detrended, peaks_idx, troughs_idx):
    """Generate sine wave aligned to specified turning point"""

    # Select turning point based on num_recent
    if align_to == 'trough':
        if len(troughs_idx) >= num_recent:
            # Use the Nth most recent (1=most recent, 3=3rd most recent, etc.)
            t_turn = troughs_idx[-num_recent]
            turn_type = 'trough'
        elif len(troughs_idx) > 0:
            t_turn = troughs_idx[-1]
            turn_type = 'trough'
        else:
            t_turn = np.argmin(detrended)
            turn_type = 'trough'
    else:  # align_to == 'peak'
        if len(peaks_idx) >= num_recent:
            t_turn = peaks_idx[-num_recent]
            turn_type = 'peak'
        elif len(peaks_idx) > 0:
            t_turn = peaks_idx[-1]
            turn_type = 'peak'
        else:
            t_turn = np.argmax(detrended)
            turn_type = 'peak'

    # Generate sine wave
    t = np.arange(len(prices))
    omega = 2 * np.pi / wavelength

    if turn_type == 'trough':
        phase_offset = -np.pi/2 - omega * t_turn
    else:
        phase_offset = np.pi/2 - omega * t_turn

    sine_wave = np.sin(omega * t + phase_offset)

    # Find sine wave peaks and troughs
    min_distance = int(wavelength * 0.4)
    sine_peaks_idx, _ = find_peaks(sine_wave, distance=min_distance)
    sine_troughs_idx, _ = find_peaks(-sine_wave, distance=min_distance)

    return sine_wave, sine_peaks_idx, sine_troughs_idx, t_turn, turn_type

def measure_alignment_accuracy(price_extrema_idx, sine_extrema_idx, wavelength):
    """Measure how well sine wave extrema align with price extrema"""
    if len(price_extrema_idx) == 0 or len(sine_extrema_idx) == 0:
        return 0, float('inf'), []

    # For each price extremum, find closest sine extremum
    distances = []
    for price_idx in price_extrema_idx:
        closest_distance = min([abs(price_idx - sine_idx) for sine_idx in sine_extrema_idx])
        distances.append(closest_distance)

    avg_distance = np.mean(distances)
    max_distance = np.max(distances)

    # Calculate percentage of wavelength
    avg_distance_pct = (avg_distance / wavelength) * 100

    return avg_distance, avg_distance_pct, distances

def test_alignment_strategy(symbol, wavelength, window_size=4000):
    """Test all alignment strategies for one instrument"""

    print(f"\n{'='*100}")
    print(f"TESTING: {symbol} {wavelength}d cycle")
    print(f"{'='*100}")

    # Load data
    dm = DataManager(symbol)
    prices, df = dm.get_data()
    dates = df['Date'].values

    if len(prices) > window_size:
        prices = prices[-window_size:]
        dates = dates[-window_size:]

    print(f"Data: {len(prices)} bars from {dates[0]} to {dates[-1]}")

    # Find actual price peaks and troughs
    price_peaks, price_troughs, detrended = find_price_extrema(prices, wavelength)

    print(f"\nActual price extrema:")
    print(f"  Peaks: {len(price_peaks)}")
    print(f"  Troughs: {len(price_troughs)}")

    # Test configurations
    align_options = ['trough', 'peak']
    num_recent_options = [1, 3, 5, 7]

    results = []

    for align_to in align_options:
        for num_recent in num_recent_options:

            # Generate sine wave
            sine_wave, sine_peaks, sine_troughs, t_turn, turn_type = generate_sine_wave_with_alignment(
                prices, wavelength, align_to, num_recent, detrended, price_peaks, price_troughs
            )

            # Measure alignment accuracy for peaks
            peak_avg_dist, peak_avg_pct, peak_distances = measure_alignment_accuracy(
                price_peaks, sine_peaks, wavelength
            )

            # Measure alignment accuracy for troughs
            trough_avg_dist, trough_avg_pct, trough_distances = measure_alignment_accuracy(
                price_troughs, sine_troughs, wavelength
            )

            # Overall score (lower is better)
            overall_score = (peak_avg_pct + trough_avg_pct) / 2

            result = {
                'align_to': align_to,
                'num_recent': num_recent,
                't_turn': int(t_turn),
                't_turn_date': str(dates[t_turn]) if t_turn < len(dates) else 'N/A',
                'turn_type': turn_type,
                'sine_peaks_count': len(sine_peaks),
                'sine_troughs_count': len(sine_troughs),
                'peak_alignment_avg_dist': peak_avg_dist,
                'peak_alignment_pct': peak_avg_pct,
                'trough_alignment_avg_dist': trough_avg_dist,
                'trough_alignment_pct': trough_avg_pct,
                'overall_score': overall_score
            }

            results.append(result)

            print(f"\n{'-'*100}")
            print(f"Config: align_to={align_to}, num_recent={num_recent}")
            print(f"  Aligned to: {turn_type} at index {t_turn} ({dates[t_turn] if t_turn < len(dates) else 'N/A'})")
            print(f"  Sine wave peaks: {len(sine_peaks)}, troughs: {len(sine_troughs)}")
            print(f"  Peak alignment: avg={peak_avg_dist:.1f} bars ({peak_avg_pct:.1f}% of wavelength)")
            print(f"  Trough alignment: avg={trough_avg_dist:.1f} bars ({trough_avg_pct:.1f}% of wavelength)")
            print(f"  Overall score: {overall_score:.1f}%")

    # Find best configuration
    best_result = min(results, key=lambda x: x['overall_score'])

    print(f"\n{'='*100}")
    print(f"BEST CONFIGURATION FOR {symbol} {wavelength}d:")
    print(f"{'='*100}")
    print(f"  Align to: {best_result['align_to']}")
    print(f"  Num recent: {best_result['num_recent']}")
    print(f"  Overall score: {best_result['overall_score']:.1f}%")
    print(f"  Peak alignment: {best_result['peak_alignment_pct']:.1f}%")
    print(f"  Trough alignment: {best_result['trough_alignment_pct']:.1f}%")

    return results, best_result

def generate_visual_html(symbol, wavelength, results, best_result):
    """Generate HTML visualization of results"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Alignment Test: {symbol} {wavelength}d</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
        h1 {{ color: #4CAF50; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #444; padding: 12px; text-align: left; }}
        th {{ background-color: #333; }}
        tr:hover {{ background-color: #2a2a2a; }}
        .best {{ background-color: #1b5e20 !important; font-weight: bold; }}
        .good {{ color: #4CAF50; }}
        .bad {{ color: #f44336; }}
    </style>
</head>
<body>
    <h1>Alignment Strategy Test: {symbol} {wavelength}d</h1>

    <h2>Test Results</h2>
    <table>
        <tr>
            <th>Align To</th>
            <th>Num Recent</th>
            <th>Aligned Date</th>
            <th>Peak Alignment</th>
            <th>Trough Alignment</th>
            <th>Overall Score</th>
        </tr>
"""

    for r in sorted(results, key=lambda x: x['overall_score']):
        row_class = 'best' if r == best_result else ''
        html += f"""
        <tr class="{row_class}">
            <td>{r['align_to']}</td>
            <td>{r['num_recent']}</td>
            <td>{r['t_turn_date']}</td>
            <td>{r['peak_alignment_pct']:.1f}%</td>
            <td>{r['trough_alignment_pct']:.1f}%</td>
            <td><b>{r['overall_score']:.1f}%</b></td>
        </tr>
"""

    html += """
    </table>

    <h2>Best Configuration</h2>
    <ul>
        <li><b>Align to:</b> {align_to}</li>
        <li><b>Num recent:</b> {num_recent}</li>
        <li><b>Overall score:</b> {overall_score:.1f}%</li>
        <li><b>Peak alignment:</b> {peak_alignment_pct:.1f}%</li>
        <li><b>Trough alignment:</b> {trough_alignment_pct:.1f}%</li>
    </ul>

    <h2>Interpretation</h2>
    <p>Lower scores are better. Score represents average distance between sine wave extrema and actual price extrema, as percentage of wavelength.</p>
</body>
</html>
""".format(**best_result)

    filename = f"/Users/bernie/Documents/Cycles Detector/Cycles Detector V14/webapp/alignment_test_{symbol}_{wavelength}d.html"
    with open(filename, 'w') as f:
        f.write(html)

    print(f"\n✅ Visual report saved: {filename}")
    return filename

# Main test
print("="*100)
print("COMPREHENSIVE ALIGNMENT STRATEGY TEST")
print("="*100)

test_cases = [
    ('AMD', 420),
    ('SPY', 420),
    ('IWM', 380)
]

all_best_results = []

for symbol, wavelength in test_cases:
    results, best_result = test_alignment_strategy(symbol, wavelength)
    all_best_results.append((symbol, wavelength, best_result))
    generate_visual_html(symbol, wavelength, results, best_result)

# Summary
print(f"\n{'='*100}")
print("SUMMARY: Best configurations across all instruments")
print(f"{'='*100}")

for symbol, wavelength, best in all_best_results:
    print(f"\n{symbol} {wavelength}d:")
    print(f"  Align to: {best['align_to']}")
    print(f"  Num recent: {best['num_recent']}")
    print(f"  Overall score: {best['overall_score']:.1f}%")

# Determine consensus
align_to_counts = {}
num_recent_counts = {}

for symbol, wavelength, best in all_best_results:
    align_to = best['align_to']
    num_recent = best['num_recent']

    align_to_counts[align_to] = align_to_counts.get(align_to, 0) + 1
    num_recent_counts[num_recent] = num_recent_counts.get(num_recent, 0) + 1

print(f"\n{'='*100}")
print("CONSENSUS RECOMMENDATION")
print(f"{'='*100}")

best_align_to = max(align_to_counts, key=align_to_counts.get)
best_num_recent = max(num_recent_counts, key=num_recent_counts.get)

print(f"\nMost common best configuration:")
print(f"  Align to: {best_align_to} ({align_to_counts[best_align_to]}/{len(test_cases)} instruments)")
print(f"  Num recent: {best_num_recent} ({num_recent_counts[best_num_recent]}/{len(test_cases)} instruments)")

print(f"\n✅ Testing complete! Check HTML files for visual results.")
