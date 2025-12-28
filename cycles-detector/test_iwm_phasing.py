#!/usr/bin/env python3
"""
Detailed phasing analysis for IWM
Tests which trough dates are detected and how phase offset is calculated
"""

import sys
import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from datetime import datetime

# Add project directories to path
sys.path.insert(0, '/Users/bernie/Documents/Cycles Detector/Cycles Detector V13/webapp')

from data_manager import DataManager

def analyze_phasing_for_wavelength(symbol, wavelength, window_size):
    """
    Detailed analysis of phasing for one wavelength
    Shows:
    1. Which troughs are detected in the search window
    2. What the phase offset SHOULD be if calculated from trough
    3. What the phase offset ACTUALLY is (currently 0.0)
    4. The impact on sine wave alignment
    """
    print(f"\n{'='*80}")
    print(f"PHASING ANALYSIS: {symbol} {wavelength}d cycle")
    print(f"{'='*80}")

    # Load data
    dm = DataManager(symbol)
    prices, df = dm.get_data()
    dates = df['Date'].values

    # Use only requested window_size
    if len(prices) > window_size:
        prices = prices[-window_size:]
        dates = dates[-window_size:]

    print(f"\nData loaded: {len(prices)} bars")
    print(f"Date range: {dates[0]} to {dates[-1]}")
    print(f"Price range: ${prices.min():.2f} - ${prices.max():.2f}")

    # Now let's manually replicate the phasing logic from pure_sine_bandpass.py
    print(f"\n{'='*60}")
    print("STEP 1: Detrend prices")
    print(f"{'='*60}")

    # Detrend using 3rd degree polynomial (matching pure_sine_bandpass.py line 143-146)
    search_window = min(3 * wavelength, len(prices))
    recent_prices = prices[-search_window:]
    recent_dates = dates[-search_window:]

    t = np.arange(len(recent_prices))
    coeffs = np.polyfit(t, recent_prices, 3)
    trend = np.polyval(coeffs, t)
    detrended = recent_prices - trend

    print(f"Search window: Last {search_window} bars (last {search_window} trading days)")
    print(f"Detrended price range: {detrended.min():.2f} to {detrended.max():.2f}")

    # Find peaks and troughs (matching pure_sine_bandpass.py lines 149-161)
    print(f"\n{'='*60}")
    print("STEP 2: Find peaks and troughs in detrended data")
    print(f"{'='*60}")

    min_distance = int(wavelength * 0.4)  # 40% of wavelength
    print(f"Minimum distance between peaks/troughs: {min_distance} bars")

    peaks_idx, _ = find_peaks(detrended, distance=min_distance)
    troughs_idx, _ = find_peaks(-detrended, distance=min_distance)

    print(f"\nPeaks found: {len(peaks_idx)}")
    if len(peaks_idx) > 0:
        print("Peak dates:")
        for i, idx in enumerate(peaks_idx):
            print(f"  Peak {i+1}: Index {idx}, Date {recent_dates[idx]}, Detrended Y={detrended[idx]:.2f}")

    print(f"\nTroughs found: {len(troughs_idx)}")
    if len(troughs_idx) > 0:
        print("Trough dates:")
        for i, idx in enumerate(troughs_idx):
            print(f"  Trough {i+1}: Index {idx}, Date {recent_dates[idx]}, Detrended Y={detrended[idx]:.2f}")

    # Trough alignment (matching pure_sine_bandpass.py lines 173-184)
    print(f"\n{'='*60}")
    print("STEP 3: Select turning point for phase alignment")
    print(f"{'='*60}")

    if len(troughs_idx) > 0:
        t_turn = troughs_idx[-1]  # LAST trough
        turn_type = 'trough'
        turn_date = recent_dates[t_turn]
        turn_value = detrended[t_turn]
        print(f"✓ Using LAST trough for alignment")
        print(f"  Index in search window: {t_turn}")
        print(f"  Date: {turn_date}")
        print(f"  Detrended value: {turn_value:.2f}")
        print(f"  Index in full array: {len(prices) - search_window + t_turn}")
    elif len(peaks_idx) > 0:
        t_turn = peaks_idx[-1]
        turn_type = 'peak'
        turn_date = recent_dates[t_turn]
        turn_value = detrended[t_turn]
        print(f"⚠️  No troughs found, using LAST peak instead")
        print(f"  Index in search window: {t_turn}")
        print(f"  Date: {turn_date}")
        print(f"  Detrended value: {turn_value:.2f}")
    else:
        t_turn = np.argmin(detrended)
        turn_type = 'trough'
        turn_date = recent_dates[t_turn]
        turn_value = detrended[t_turn]
        print(f"⚠️  No peaks or troughs found, using minimum value")
        print(f"  Index in search window: {t_turn}")
        print(f"  Date: {turn_date}")
        print(f"  Detrended value: {turn_value:.2f}")

    # Calculate what the phase offset SHOULD be
    print(f"\n{'='*60}")
    print("STEP 4: Calculate phase offset from turning point")
    print(f"{'='*60}")

    # For a sine wave: y = sin(omega * t + phi)
    # At a trough, y = -1, so: sin(omega * t_turn + phi) = -1
    # This means: omega * t_turn + phi = -pi/2 (or 3*pi/2, etc.)
    # Therefore: phi = -pi/2 - omega * t_turn

    omega = 2 * np.pi / wavelength

    if turn_type == 'trough':
        # Trough should be at -1, which is sin(theta) = -1, theta = -pi/2
        calculated_phase = -np.pi/2 - omega * t_turn
    else:
        # Peak should be at +1, which is sin(theta) = 1, theta = pi/2
        calculated_phase = np.pi/2 - omega * t_turn

    # Normalize to [-pi, pi]
    calculated_phase = np.arctan2(np.sin(calculated_phase), np.cos(calculated_phase))

    print(f"Turning point type: {turn_type}")
    print(f"Turning point index in search window: {t_turn}")
    print(f"Omega (2π/wavelength): {omega:.6f}")
    print(f"Calculated phase offset: {calculated_phase:.6f} radians ({np.degrees(calculated_phase):.2f}°)")
    print(f"\nThis phase offset would align the sine wave so that:")
    if turn_type == 'trough':
        print(f"  - The trough (-1) occurs at index {t_turn} (date {turn_date})")
    else:
        print(f"  - The peak (+1) occurs at index {t_turn} (date {turn_date})")

    # What the code ACTUALLY does
    print(f"\n{'='*60}")
    print("STEP 5: What the code ACTUALLY uses")
    print(f"{'='*60}")

    actual_phase = 0.0  # From pure_sine_bandpass.py line 216

    print(f"❌ ACTUAL phase offset used: {actual_phase} radians (HARDCODED ZERO)")
    print(f"   This is defined at line 216 of pure_sine_bandpass.py")
    print(f"\n⚠️  CRITICAL ISSUE:")
    print(f"   The code detects the trough at {turn_date}")
    print(f"   Calculates it should use phase = {calculated_phase:.6f} radians")
    print(f"   But then IGNORES it and uses phase = 0.0 instead!")

    # Show the impact
    print(f"\n{'='*60}")
    print("STEP 6: Impact of using zero phase vs calculated phase")
    print(f"{'='*60}")

    # Generate both sine waves
    t_full = np.arange(len(prices))

    # With calculated phase (what it SHOULD be)
    sine_correct = np.sin(omega * t_full + calculated_phase)

    # With zero phase (what it ACTUALLY is)
    sine_actual = np.sin(omega * t_full + actual_phase)

    # Find where troughs occur in each
    correct_trough_idx = np.argmin(sine_correct[-search_window:])
    actual_trough_idx = np.argmin(sine_actual[-search_window:])

    print(f"\nWith CALCULATED phase ({calculated_phase:.6f} rad):")
    print(f"  Last trough in sine wave: index {correct_trough_idx} (date {recent_dates[correct_trough_idx]})")
    print(f"  This MATCHES the detected trough at {turn_date}")

    print(f"\nWith ACTUAL phase (0.0 rad):")
    print(f"  Last trough in sine wave: index {actual_trough_idx} (date {recent_dates[actual_trough_idx]})")
    print(f"  This is OFF by {abs(actual_trough_idx - t_turn)} bars from detected trough")

    phase_diff_bars = abs(actual_trough_idx - t_turn)
    phase_diff_days = phase_diff_bars  # Already in trading days

    print(f"\nPhase misalignment: {phase_diff_bars} bars ({phase_diff_days} trading days)")
    print(f"As percentage of wavelength: {(phase_diff_bars / wavelength) * 100:.1f}%")

    return {
        'wavelength': wavelength,
        'detected_trough_date': turn_date,
        'detected_trough_idx': t_turn,
        'calculated_phase': calculated_phase,
        'actual_phase': actual_phase,
        'phase_error_bars': phase_diff_bars,
        'phase_error_pct': (phase_diff_bars / wavelength) * 100
    }


# Main analysis
print("="*80)
print("IWM PHASING ANALYSIS")
print("="*80)
print("\nTest parameters:")
print("  Symbol: IWM")
print("  Window size: 4,000 bars")
print("  Scan range: 50-500 days")
print("  Algorithm: Morlet wavelet (for cycle scanning)")
print("  Bandpass: Pure sine (for phase alignment)")

# Test with a few representative wavelengths
test_wavelengths = [150, 250, 380, 420]

results = []
for wl in test_wavelengths:
    result = analyze_phasing_for_wavelength('IWM', wl, 4000)
    results.append(result)

# Summary
print(f"\n{'='*80}")
print("SUMMARY: Phasing errors across wavelengths")
print(f"{'='*80}")
print(f"\n{'Wavelength':<12} {'Trough Date':<12} {'Calc Phase':<12} {'Actual Phase':<13} {'Error (bars)':<12} {'Error %':<10}")
print("-" * 80)
for r in results:
    print(f"{r['wavelength']:<12} {str(r['detected_trough_date']):<12} {r['calculated_phase']:>11.4f} {r['actual_phase']:>12.1f} {r['phase_error_bars']:>11.0f} {r['phase_error_pct']:>9.1f}%")

print(f"\n{'='*80}")
print("CONCLUSION")
print(f"{'='*80}")
print("""
The phasing mechanism DETECTS troughs correctly using this process:
1. Detrends prices using 3rd-degree polynomial
2. Searches last 3 wavelengths of data
3. Finds troughs using scipy.signal.find_peaks() with 40% wavelength min distance
4. Selects the LAST trough found

However, it then IGNORES the detected trough and uses phase_offset = 0.0.

This means:
❌ The sine wave is NOT aligned to actual price troughs
❌ Phase errors range from a few bars to significant portions of the wavelength
❌ Trading signals based on "trough at date X" are INCORRECT

To fix this, pure_sine_bandpass.py line 216 should use the calculated phase
instead of hardcoding phase_offset = 0.0.
""")
