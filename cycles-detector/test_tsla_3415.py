#!/usr/bin/env python3
"""Generate TSLA heatmap matching SIGMA-L parameters"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from matplotlib.colors import LinearSegmentedColormap
import sys

sys.path.append('algorithms/heatmap')
from heatmap_algo import process_week_on_grid

# Load TSLA data (3415 points to match SIGMA-L)
prices = np.loadtxt('tsla_prices_3415.txt')
print(f"Loaded {len(prices)} TSLA price points")

# EXACT SIGMA-L parameters for TSLA (shorter cycles)
wavelengths = np.arange(50, 301, 2)  # 50-300 days, step 2 (finer resolution)
print(f"Scanning {len(wavelengths)} wavelengths: {wavelengths[0]}-{wavelengths[-1]} days")

# Process heatmap (use FULL sample, no window)
total_weeks = 200
week_step = 2
actual_weeks = total_weeks // week_step
heatmap = np.zeros((len(wavelengths), actual_weeks))

print("Processing weeks...")
for i, week in enumerate(range(0, total_weeks, week_step)):
    spectrum = process_week_on_grid(prices, week, wavelengths, window_size=None)
    time_idx = actual_weeks - 1 - i
    heatmap[:, time_idx] = spectrum

    if i % 20 == 0:
        print(f"  {i}/{actual_weeks}")

# Get most recent spectrum
most_recent = heatmap[:, -1]

# Create visualization
plt.style.use('dark_background')
fig = plt.figure(figsize=(20, 8))

ax1 = plt.subplot2grid((1, 6), (0, 0), colspan=5)
ax2 = plt.subplot2grid((1, 6), (0, 5), colspan=1)

# Purple colormap (SIGMA-L style)
colors = ['#000000', '#1a0033', '#330066', '#6600cc', '#9933ff', '#ddaaff', '#ffffff']
purple_cmap = LinearSegmentedColormap.from_list('purple', colors, N=256)

# Display heatmap with ABSOLUTE scaling (no normalization per-week)
im = ax1.imshow(heatmap, aspect='auto', cmap=purple_cmap,
                extent=[0, actual_weeks, wavelengths[0], wavelengths[-1]],
                origin='lower', interpolation='bilinear',
                vmin=0, vmax=1.5)  # Fixed scale like SIGMA-L

ax1.set_xlabel('Time (weeks ago)', color='white', fontsize=12)
ax1.set_ylabel('Wavelength (Days)', color='white', fontsize=12)
ax1.set_title('TSLA - SIGMA-L Style (3415 samples)', color='cyan', pad=15, fontsize=14)

# Time labels
ax1.set_xticks([0, actual_weeks//4, actual_weeks//2, 3*actual_weeks//4, actual_weeks-1])
years_back = actual_weeks * 7 / 365
ax1.set_xticklabels([f'{years_back:.0f}yr', f'{years_back*0.75:.0f}yr',
                      f'{years_back*0.5:.0f}yr', f'{years_back*0.25:.0f}yr', 'Now'], color='gray')

ax1.set_yticks(range(50, 350, 50))
ax1.grid(True, alpha=0.3)

# Power spectrum
ax2.barh(wavelengths, most_recent,
         height=wavelengths[1] - wavelengths[0],
         color='purple', alpha=0.7, edgecolor='none')

ax2.set_ylim(wavelengths[0], wavelengths[-1])
ax2.set_xlim(0, np.max(most_recent) * 1.2)
ax2.set_xlabel('Power', color='white', fontsize=10)
ax2.set_title('Current\nSpectrum', color='white', fontsize=10)
ax2.grid(True, alpha=0.2, axis='x')

# Find peaks (adjust threshold for shorter wavelengths)
peaks, _ = find_peaks(most_recent, height=0.3, distance=5)
sorted_peaks = peaks[np.argsort(most_recent[peaks])[::-1]]

print("\nTop detected cycles:")
for i, peak_idx in enumerate(sorted_peaks[:8]):
    wl = wavelengths[peak_idx]
    power = most_recent[peak_idx]
    print(f"  {i+1}. {wl:3.0f} days: {power:.3f}")

    # Label on plot
    ax2.text(power + 0.02, wl, f'{wl:.0f}d',
            color='yellow', fontsize=9, va='center', weight='bold')

    # Line on heatmap
    ax1.axhline(y=wl, color='cyan', alpha=0.3, linestyle='--', linewidth=0.8)

ax2.set_yticklabels([])

# Clean spines
for ax in [ax1, ax2]:
    for spine in ax.spines.values():
        spine.set_visible(False)

plt.subplots_adjust(wspace=0.05)
plt.tight_layout()

plt.savefig('tsla_sigma_l_match.png', dpi=150, facecolor='black', bbox_inches='tight')
print("\n✓ Saved: tsla_sigma_l_match.png")
print(f"\nSample: {len(prices)} points (matches SIGMA-L)")