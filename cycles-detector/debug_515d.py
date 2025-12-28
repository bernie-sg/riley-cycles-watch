#!/usr/bin/env python3
"""
Debug why 515d peak detection fails
"""

import requests
import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

def apply_phase_shift(values, shift):
    if shift == 0:
        return values
    return values[shift:] + values[:shift]

def scale_bandpass(bandpass):
    mean = sum(bandpass) / len(bandpass)
    centered = [v - mean for v in bandpass]
    scale_factor = 0.8
    scaled = [v * scale_factor for v in centered]
    return scaled

# Fetch 515d data
url = "http://localhost:5001/api/bandpass?symbol=IWM&selected_wavelength=515&window_size=4000"
response = requests.get(url)
data = response.json()

raw_bandpass = data['bandpass']['scaled_values']
shifted_bandpass = apply_phase_shift(raw_bandpass, 0)
scaled_bandpass = scale_bandpass(shifted_bandpass)

print(f"515d Bandpass Analysis:")
print(f"Length: {len(scaled_bandpass)}")
print(f"Min: {min(scaled_bandpass):.2f}")
print(f"Max: {max(scaled_bandpass):.2f}")
print(f"First 20 values: {[f'{v:.2f}' for v in scaled_bandpass[:20]]}")
print(f"Values at indices 100-120: {[f'{v:.2f}' for v in scaled_bandpass[100:120]]}")

# Check for local maxima manually
print(f"\nSearching for local maxima in first 500 points:")
local_maxima = []
for i in range(1, min(500, len(scaled_bandpass) - 1)):
    if scaled_bandpass[i] > scaled_bandpass[i-1] and scaled_bandpass[i] > scaled_bandpass[i+1]:
        local_maxima.append((i, scaled_bandpass[i]))

print(f"Found {len(local_maxima)} local maxima")
if len(local_maxima) > 0:
    print(f"First 10 local maxima:")
    for idx, val in local_maxima[:10]:
        print(f"  idx={idx}, value={val:.2f}")
else:
    print("NO LOCAL MAXIMA FOUND - this is the problem!")
    print("\nChecking if bandpass is flat or has very small variations:")
    print(f"Standard deviation: {(sum((v - sum(scaled_bandpass)/len(scaled_bandpass))**2 for v in scaled_bandpass) / len(scaled_bandpass))**0.5:.4f}")

    # Check first derivative
    print("\nFirst 20 differences (should show up/down pattern for sine wave):")
    diffs = [scaled_bandpass[i+1] - scaled_bandpass[i] for i in range(20)]
    print([f'{d:.4f}' for d in diffs])

# Create a plot to visualize
plt.figure(figsize=(15, 6))
plt.plot(scaled_bandpass[:1000], label='Scaled Bandpass (515d)', linewidth=0.5)
plt.axhline(y=0, color='gray', linestyle='--', linewidth=0.5)
plt.axhline(y=20, color='red', linestyle='--', linewidth=0.5, alpha=0.3)
plt.axhline(y=-20, color='lime', linestyle='--', linewidth=0.5, alpha=0.3)
plt.title('IWM 515d Bandpass - First 1000 points')
plt.xlabel('Index')
plt.ylabel('Value')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('/Users/bernie/Documents/Cycles Detector/Cycles Detector V13/webapp/debug_515d_bandpass.png', dpi=150)
print(f"\nPlot saved to: debug_515d_bandpass.png")
