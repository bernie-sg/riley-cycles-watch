#!/usr/bin/env python3
"""
Systematic testing to match SIGMA-L TLT spectrum
Target: Single dominant peak around 525d
"""

import numpy as np
from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

def create_morlet(freq, length, q_divisor, q_cap):
    """Create Morlet wavelet"""
    wavelength = 1.0 / freq
    Q = min(wavelength / q_divisor, q_cap)
    sigma = Q / (2.0 * np.pi * freq)

    t = np.arange(length) - length/2.0
    envelope = np.exp(-t**2 / (2.0 * sigma**2))
    carrier = np.exp(1j * 2.0 * np.pi * freq * t)
    wavelet = envelope * carrier

    norm = np.sqrt(np.sum(np.abs(wavelet)**2))
    wavelet /= norm

    return wavelet

def compute_power(data, wavelength, q_divisor, q_cap):
    """Compute power"""
    n = len(data)
    if wavelength > n//2:
        return 0

    freq = 1.0 / wavelength
    cycles = min(8, max(4, n // wavelength))
    wlen = min(n, wavelength * cycles)

    wavelet = create_morlet(freq, wlen, q_divisor, q_cap)

    max_power = 0
    step = max(1, wavelength // 8)

    for center in range(wlen//2, n - wlen//2 + 1, step):
        start_idx = center - wlen//2
        end_idx = start_idx + wlen

        if start_idx >= 0 and end_idx <= n:
            signal_segment = data[start_idx:end_idx]
            conv = np.sum(signal_segment * np.conj(wavelet))
            power = np.abs(conv)**2
            max_power = max(max_power, power)

    return np.sqrt(max_power) if max_power > 0 else 0

def test_configuration(prices, q_divisor, q_cap, smooth_sigma, normalize_method):
    """Test a specific configuration"""
    # Preprocess
    data = np.log(prices)
    x = np.arange(len(data))
    coeffs = np.polyfit(x, data, 1)
    trend = np.polyval(coeffs, x)
    data = data - trend

    # Compute spectrum
    wavelengths = np.arange(100, 801, 1)
    spectrum = np.array([compute_power(data, wl, q_divisor, q_cap) for wl in wavelengths])

    # Smoothing
    if smooth_sigma > 0:
        spectrum = gaussian_filter1d(spectrum, sigma=smooth_sigma, mode='nearest')

    # Normalization
    if normalize_method == 'max':
        spectrum = spectrum / np.max(spectrum)
    elif normalize_method == 'percentile95':
        p95 = np.percentile(spectrum, 95)
        spectrum = spectrum / p95
        spectrum = np.clip(spectrum, 0, 1)
    elif normalize_method == 'none':
        pass

    # Find peak
    peak_idx = np.argmax(spectrum)
    peak_wl = wavelengths[peak_idx]
    peak_power = spectrum[peak_idx]

    # Calculate dominance ratio (peak / second highest)
    spectrum_copy = spectrum.copy()
    spectrum_copy[peak_idx] = 0
    second_peak = np.max(spectrum_copy)
    dominance = peak_power / second_peak if second_peak > 0 else 0

    return peak_wl, peak_power, dominance, spectrum, wavelengths

# Load data
print("Loading TLT data...")
prices = np.loadtxt('tlt_prices.txt')
print(f"Loaded {len(prices)} points\n")

print("=" * 80)
print("SYSTEMATIC PARAMETER SWEEP")
print("=" * 80)
print("Target: Peak at ~525d with high dominance ratio (>2.0)")
print("-" * 80)

# Test configurations
best_config = None
best_score = 0

test_configs = []

# Q divisors to test
for q_div in [40, 50, 60, 70, 80, 90, 100]:
    # Q caps to test
    for q_cap in [8, 10, 12, 15]:
        # Smoothing sigmas to test
        for smooth in [0, 3, 5, 8, 10, 15]:
            # Normalization methods
            for norm in ['max', 'percentile95', 'none']:
                test_configs.append((q_div, q_cap, smooth, norm))

print(f"Testing {len(test_configs)} configurations...\n")

results = []

for i, (q_div, q_cap, smooth, norm) in enumerate(test_configs):
    peak_wl, peak_power, dominance, spectrum, wavelengths = test_configuration(
        prices, q_div, q_cap, smooth, norm
    )

    # Score based on:
    # 1. How close to 525d (target)
    # 2. Dominance ratio (higher is better)
    distance_from_target = abs(peak_wl - 525)
    if distance_from_target <= 10:  # Within 10 days of target
        score = dominance * (1.0 - distance_from_target / 50.0)
    else:
        score = 0

    results.append({
        'q_div': q_div,
        'q_cap': q_cap,
        'smooth': smooth,
        'norm': norm,
        'peak_wl': peak_wl,
        'peak_power': peak_power,
        'dominance': dominance,
        'score': score,
        'spectrum': spectrum,
        'wavelengths': wavelengths
    })

    if score > best_score:
        best_score = score
        best_config = results[-1]

    if (i + 1) % 50 == 0:
        print(f"  Tested {i + 1}/{len(test_configs)} configs...")

# Sort by score
results.sort(key=lambda x: x['score'], reverse=True)

print("\n" + "=" * 80)
print("TOP 10 CONFIGURATIONS")
print("=" * 80)
print(f"{'Q/Cap':<12} {'Smooth':<8} {'Norm':<15} {'Peak':<8} {'Dominance':<12} {'Score':<8}")
print("-" * 80)

for r in results[:10]:
    print(f"{r['q_div']}/{r['q_cap']:<8} {r['smooth']:<8} {r['norm']:<15} "
          f"{r['peak_wl']}d{'':<4} {r['dominance']:<12.2f} {r['score']:<8.2f}")

print("\n" + "=" * 80)
print("BEST CONFIGURATION")
print("=" * 80)
if best_config:
    print(f"Q divisor: {best_config['q_div']}")
    print(f"Q cap: {best_config['q_cap']}")
    print(f"Smoothing sigma: {best_config['smooth']}")
    print(f"Normalization: {best_config['norm']}")
    print(f"Peak wavelength: {best_config['peak_wl']}d")
    print(f"Peak power: {best_config['peak_power']:.3f}")
    print(f"Dominance ratio: {best_config['dominance']:.2f}")
    print(f"Score: {best_config['score']:.2f}")

    # Save visualization
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(12, 4))

    spec = best_config['spectrum']
    wls = best_config['wavelengths']

    # Normalize for display
    spec_norm = spec / np.max(spec)

    ax.fill_between(wls, 0, spec_norm, color='#8844ff', alpha=0.6)
    ax.plot(wls, spec_norm, color='white', linewidth=1, alpha=0.8)
    ax.axvline(best_config['peak_wl'], color='yellow', linestyle='--', linewidth=2, alpha=0.7)

    ax.set_facecolor('#0a0a0a')
    ax.set_xlabel('Wavelength (days)', color='white')
    ax.set_ylabel('Normalized Power', color='white')
    ax.set_title(f'Best Match - Peak at {best_config["peak_wl"]}d', color='cyan')
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.savefig('best_spectrum_match.png', dpi=120, facecolor='#0a0a0a')
    print("\nSaved visualization: best_spectrum_match.png")
else:
    print("No configuration found matching target criteria")