#!/usr/bin/env python3
"""
Diagnostic: Check 625d cycle in heatmap vs current power spectrum
"""
import numpy as np
import sys
sys.path.insert(0, '/Users/bernie/Documents/Cycles Detector/Cycles Detector V6/webapp')

from algorithms.heatmap.heatmap_algo import process_week_on_grid, compute_power, apply_scanner_processing

# Load TLT data
prices = np.loadtxt('tlt_history.csv', delimiter=',', skiprows=1, usecols=1)
print(f"Loaded {len(prices)} TLT price points")

# Define wavelengths (same as heatmap)
trading_wavelengths = np.arange(100, 801, 5)
calendar_wavelengths = trading_wavelengths * 1.451

# Find index for 625d calendar days
# 625 / 1.451 = ~431 trading days
target_trading = 625 / 1.451  # ~431 trading days
idx_625 = np.argmin(np.abs(trading_wavelengths - target_trading))
actual_calendar = calendar_wavelengths[idx_625]

print(f"\nTarget: 625 calendar days")
print(f"Trading days: {trading_wavelengths[idx_625]:.0f}")
print(f"Calendar days: {actual_calendar:.0f}")
print(f"Index in array: {idx_625}")

# Check current spectrum (week 0)
print("\n" + "="*60)
print("CURRENT SPECTRUM (Most Recent)")
print("="*60)
current_spectrum = process_week_on_grid(prices, 0, trading_wavelengths, window_size=4000)
print(f"625d power (current): {current_spectrum[idx_625]:.3f}")

# Find top 5 peaks in current spectrum
top_indices = np.argsort(current_spectrum)[-5:][::-1]
print("\nTop 5 peaks in current spectrum:")
for i, idx in enumerate(top_indices, 1):
    cal_wl = calendar_wavelengths[idx]
    power = current_spectrum[idx]
    marker = " ← 625d region" if abs(cal_wl - 625) < 20 else ""
    print(f"  {i}. {cal_wl:.0f}d: power={power:.3f}{marker}")

# Check historical values at 625d
print("\n" + "="*60)
print("HISTORICAL VALUES at 625d wavelength")
print("="*60)

weeks_to_check = [0, 26, 52, 104, 156, 208, 260]  # Now, 6mo, 1yr, 2yr, 3yr, 4yr, 5yr
print("\nWeek | Years Ago | Power at 625d")
print("-" * 40)

historical_625d = []
for week in weeks_to_check:
    spectrum = process_week_on_grid(prices, week, trading_wavelengths, window_size=4000)
    power_625 = spectrum[idx_625]
    years_ago = week / 52
    print(f"{week:4d} | {years_ago:5.1f}     | {power_625:.3f}")
    historical_625d.append(power_625)

# Analysis
print("\n" + "="*60)
print("ANALYSIS")
print("="*60)

current = historical_625d[0]
historical_avg = np.mean(historical_625d[1:])
historical_max = np.max(historical_625d[1:])

print(f"\nCurrent 625d power: {current:.3f}")
print(f"Historical average:  {historical_avg:.3f}")
print(f"Historical maximum:  {historical_max:.3f}")
print(f"\nRatio (current/avg): {current/historical_avg if historical_avg > 0 else 0:.2f}x")

if current > 2 * historical_avg:
    print("\n⚠️  NEWLY EMERGING CYCLE")
    print("   The 625d cycle is much stronger now than historically.")
    print("   This explains why it's bright in power spectrum but weak in heatmap.")
elif current < 0.5 * historical_max:
    print("\n⚠️  CYCLE WEAKENING")
    print("   The 625d cycle was stronger in the past.")
else:
    print("\n✓  CONSISTENT CYCLE")
    print("   The 625d cycle has similar strength historically.")

# Check suppression filter
print("\n" + "="*60)
print("SUPPRESSION FILTER CHECK")
print("="*60)
print(f"\nHigh-pass filter cutoff: ~600 trading days")
print(f"625 calendar days = {625/1.451:.0f} trading days")
print(f"Distance from cutoff: {625/1.451 - 600:.0f} trading days")
print("\n⚠️  The 625d cycle is ABOVE the 600-day cutoff,")
print("   so it may be partially suppressed by the high-pass filter.")
