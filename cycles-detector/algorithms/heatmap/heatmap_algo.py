#!/usr/bin/env python3
"""
HEATMAP ALGORITHM - Fast Version with Fixed Grid Alignment
==========================================================
Optimized for speed with coarser grid while maintaining alignment.
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from matplotlib.colors import LinearSegmentedColormap

def create_high_q_morlet(freq, length):
    """Morlet wavelet with UNIFORM Q for all wavelengths"""
    # UNIFORM Q: Same sharpness for all cycles (no wavelength bias)
    # This ensures short and long cycles are detected with equal sensitivity
    Q = 50.0  # Maximum sharpness for best component yield, no wavelength bias
    sigma = Q / (2.0 * np.pi * freq)

    t = np.arange(length) - length/2.0
    envelope = np.exp(-t**2 / (2.0 * sigma**2))
    carrier = np.exp(1j * 2.0 * np.pi * freq * t)
    wavelet = envelope * carrier

    norm = np.sqrt(np.sum(np.abs(wavelet)**2))
    wavelet /= norm

    return wavelet

def compute_power(data, wavelength):
    """EXACT scanner_clean power computation"""
    n = len(data)
    if wavelength > n//2:
        return 0

    freq = 1.0 / wavelength
    cycles = min(8, max(4, n // wavelength))
    wlen = min(n, wavelength * cycles)

    wavelet = create_high_q_morlet(freq, wlen)

    total_power = 0
    count = 0
    step = max(1, wavelength // 8)

    for center in range(wlen//2, n - wlen//2 + 1, step):
        start_idx = center - wlen//2
        end_idx = start_idx + wlen

        if start_idx >= 0 and end_idx <= n:
            signal_segment = data[start_idx:end_idx]
            conv = np.sum(signal_segment * np.conj(wavelet))
            total_power += np.abs(conv)**2
            count += 1

    return np.sqrt(total_power / count) if count > 0 else 0

def apply_scanner_processing(spectrum):
    """Simplified processing for speed"""
    n = len(spectrum)

    # Simple median filter
    filtered = np.zeros(n)
    for i in range(n):
        start = max(0, i-1)
        end = min(n, i+2)
        filtered[i] = np.median(spectrum[start:end])

    # Simple smoothing
    smoothed = np.convolve(filtered, np.ones(5)/5, mode='same')

    # Peak enhancement
    mean_val = np.mean(smoothed)
    enhanced = smoothed.copy()
    enhanced[smoothed > mean_val] = mean_val + (smoothed[smoothed > mean_val] - mean_val) * 2

    return enhanced

def process_week_on_grid(prices, week, trading_wavelengths, window_size=None, suppress_long_cycles=True,
                         normalize=True, highpass_max_period=600, highpass_min_threshold=50):
    """Fast processing on fixed grid

    Args:
        window_size: MUST match power spectrum window for consistency
        suppress_long_cycles: Apply high-pass filter (optional)
        normalize: If True, normalize to max=1.0 (per-week). If False, return raw processed values
        highpass_max_period: Maximum period for high-pass filter (default: 600)
        highpass_min_threshold: Minimum threshold for applying filter (default: 50)
    """
    rollback = week * 5
    end_idx = len(prices) - rollback

    # Use same window as power spectrum
    if window_size is None:
        window_size = end_idx

    start_idx = end_idx - window_size

    if start_idx < 0 or end_idx <= 0:
        return np.zeros(len(trading_wavelengths))

    # Extract and preprocess
    price_window = prices[start_idx:end_idx]

    # Handle negative prices (shift to positive range before log)
    min_price = np.min(price_window)
    if min_price <= 0:
        price_window = price_window - min_price + 1.0

    data = np.log(price_window)

    # Optional high-pass filter to suppress long cycles
    if suppress_long_cycles:
        long_ma_period = min(highpass_max_period, len(data) // 3)
        if long_ma_period > highpass_min_threshold:
            kernel = np.ones(long_ma_period) / long_ma_period
            pad_width = long_ma_period // 2
            data_padded = np.pad(data, pad_width, mode='edge')
            long_ma = np.convolve(data_padded, kernel, mode='valid')
            if len(long_ma) > len(data):
                trim = (len(long_ma) - len(data)) // 2
                long_ma = long_ma[trim:trim+len(data)]
            data = data - long_ma[:len(data)]

    # Simple linear detrend
    x = np.arange(len(data))
    coeffs = np.polyfit(x, data, 1)
    trend = np.polyval(coeffs, x)
    data = data - trend

    # Compute spectrum
    spectrum = np.array([compute_power(data, wl) for wl in trading_wavelengths])

    # Process
    spectrum = apply_scanner_processing(spectrum)

    # Normalize (optional - allows global normalization later)
    if normalize:
        max_val = np.max(spectrum)
        if max_val > 0:
            spectrum /= max_val

    return spectrum

def main(prices=None, symbol='TLT'):
    """
    Generate heatmap for cycle analysis

    Args:
        prices: Price array (if None, will try to load from file)
        symbol: Symbol name for file loading (default: TLT)
    """
    print("HEATMAP ALGORITHM FAST - Fixed Grid")
    print("====================================")

    # Load data if not provided
    if prices is None:
        try:
            prices = np.loadtxt(f'{symbol.lower()}_prices.txt')
        except:
            print(f"Error loading {symbol.lower()}_prices.txt")
            return

    print(f"Loaded {len(prices)} price points")

    # COARSE GRID for speed - step of 5
    trading_wavelengths = np.arange(100, 801, 5)  # Coarser grid
    calendar_wavelengths = trading_wavelengths * 1.451

    print(f"Grid: {len(trading_wavelengths)} points")

    # Process fewer weeks for speed
    total_weeks = 200  # Reduced from 260
    week_step = 2  # Process every other week

    actual_weeks = total_weeks // week_step
    heatmap = np.zeros((len(trading_wavelengths), actual_weeks))

    print("Processing weeks...")
    for i, week in enumerate(range(0, total_weeks, week_step)):
        spectrum = process_week_on_grid(prices, week, trading_wavelengths)
        time_idx = actual_weeks - 1 - i
        heatmap[:, time_idx] = spectrum

        if i % 20 == 0:
            print(f"  Processed {i}/{actual_weeks}")

    # Get most recent spectrum for power plot
    most_recent = heatmap[:, -1]

    # Create visualization
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 5))

    ax1 = plt.subplot2grid((1, 6), (0, 0), colspan=5)
    ax2 = plt.subplot2grid((1, 6), (0, 5), colspan=1)

    # Purple colormap
    colors = ['#000000', '#2a0050', '#5500aa', '#8833ff', '#bb66ff', '#ddaaff', '#ffffff']
    purple_cmap = LinearSegmentedColormap.from_list('purple', colors, N=256)

    # Display heatmap
    im = ax1.imshow(heatmap, aspect='auto', cmap=purple_cmap,
                    extent=[0, actual_weeks, calendar_wavelengths[0], calendar_wavelengths[-1]],
                    origin='lower', interpolation='bilinear',
                    vmin=0.15, vmax=0.8)

    ax1.set_xlabel('Time (weeks ago)', color='white')
    ax1.set_ylabel('Wavelength (Calendar Days)', color='white')
    ax1.set_title('HEATMAP - Fixed Grid Alignment', color='cyan', pad=15)

    # Time labels
    ax1.set_xticks([0, actual_weeks//4, actual_weeks//2, 3*actual_weeks//4, actual_weeks-1])
    ax1.set_xticklabels(['4yr', '3yr', '2yr', '1yr', 'Now'], color='gray')

    # Y-axis
    ax1.set_yticks(range(200, 1200, 200))
    ax1.grid(True, alpha=0.3)

    # Power spectrum with SAME grid
    ax2.barh(calendar_wavelengths, most_recent,
             height=calendar_wavelengths[1] - calendar_wavelengths[0],
             color='purple', alpha=0.7)

    # EXACT same Y limits
    ax2.set_ylim(calendar_wavelengths[0], calendar_wavelengths[-1])
    ax2.set_xlim(0, 1.2)
    ax2.set_xlabel('Power', color='white', fontsize=10)
    ax2.set_title('Current', color='white', fontsize=10)
    ax2.grid(True, alpha=0.2)

    # Find peaks
    peaks, _ = find_peaks(most_recent, height=0.15, distance=5)

    print("\nDetected peaks:")
    for peak_idx in peaks[:5]:  # Top 5 peaks
        wl = calendar_wavelengths[peak_idx]
        power = most_recent[peak_idx]
        print(f"  {wl:.0f}d: {power:.2f}")

        # Label on plot
        ax2.text(power + 0.02, wl, f'{wl:.0f}d',
                color='white', fontsize=8, va='center')

        # Alignment line
        ax1.axhline(y=wl, color='cyan', alpha=0.2, linestyle='--', linewidth=0.5)

    ax2.set_yticklabels([])

    # Clean up
    for ax in [ax1, ax2]:
        for spine in ax.spines.values():
            spine.set_visible(False)

    plt.subplots_adjust(wspace=0)
    plt.tight_layout()

    plt.savefig('heatmap_algo_fast.png', dpi=120, facecolor='black')
    print("\nSaved: heatmap_algo_fast.png")
    print("Grid alignment maintained with faster processing")

if __name__ == "__main__":
    main()