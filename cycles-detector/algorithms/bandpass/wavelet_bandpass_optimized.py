#!/usr/bin/env python3
"""
Weighted Morlet Wavelet Bandpass with Phase Optimization
=========================================================

Based on SIGMA-L: The bandpass is derived from weighted wavelet analysis,
but the phase is optimized to align peaks/troughs with actual price extremes.

Key insight from SIGMA-L images: The sine wave PERFECTLY aligns with price
peaks (red dots) and troughs (green dots). This requires phase optimization.
"""

import numpy as np
from scipy.signal import find_peaks, argrelextrema
from wavelet_bandpass import compute_wavelet_coefficients


def find_price_extremes(prices, wavelength, recent_cycles=3):
    """
    Find recent price peaks and troughs

    Args:
        prices: Price data
        wavelength: Expected wavelength for peak detection
        recent_cycles: Number of recent cycles to analyze

    Returns:
        peaks_idx: Indices of peaks
        troughs_idx: Indices of troughs
    """
    # Look at recent data (last N cycles)
    recent_length = int(wavelength * recent_cycles)
    recent_data = prices[-recent_length:]

    # Use detrended data for peak finding
    log_prices = np.log(recent_data)
    x = np.arange(len(log_prices))
    coeffs = np.polyfit(x, log_prices, 1)
    trend = np.polyval(coeffs, x)
    detrended = log_prices - trend

    # Find peaks with distance constraint based on wavelength
    # Peaks should be at least wavelength/2 apart
    min_distance = int(wavelength * 0.4)  # 40% of wavelength

    peaks_idx, _ = find_peaks(detrended, distance=min_distance)
    troughs_idx, _ = find_peaks(-detrended, distance=min_distance)

    # Convert to absolute indices
    offset = len(prices) - recent_length
    peaks_idx = peaks_idx + offset
    troughs_idx = troughs_idx + offset

    return peaks_idx, troughs_idx


def optimize_phase(prices, wavelength, initial_phase, amplitude):
    """
    Optimize phase to align sine wave with price peaks and troughs

    Strategy:
    1. Find recent price peaks and troughs
    2. Try different phase offsets around initial_phase
    3. Score each phase by how well sine peaks/troughs align with price extremes
    4. Return best phase

    Args:
        prices: Price data
        wavelength: Wavelength in days
        initial_phase: Initial phase from wavelet analysis
        amplitude: Amplitude from wavelet analysis

    Returns:
        optimized_phase: Best phase in radians
        alignment_score: Quality score (0-1, higher is better)
    """
    # Find price extremes
    peaks_idx, troughs_idx = find_price_extremes(prices, wavelength)

    if len(peaks_idx) == 0 and len(troughs_idx) == 0:
        # No extremes found, use initial phase
        return initial_phase, 0.0

    # Detrend prices for comparison
    log_prices = np.log(prices)
    x = np.arange(len(log_prices))
    coeffs = np.polyfit(x, log_prices, 1)
    trend = np.polyval(coeffs, x)
    detrended = log_prices - trend

    # Try different phase offsets
    omega = 2 * np.pi / wavelength
    n = len(prices)
    t = np.arange(n)

    # Search range: ±π/2 around initial phase (±90°)
    phase_offsets = np.linspace(-np.pi/2, np.pi/2, 91)  # 2° resolution

    best_score = -np.inf
    best_phase = initial_phase

    for phase_offset in phase_offsets:
        test_phase = initial_phase + phase_offset

        # Generate sine wave with this phase
        sine_wave = amplitude * np.sin(omega * t + test_phase)

        # Find where sine wave has peaks and troughs
        sine_peaks_idx, _ = find_peaks(sine_wave, distance=int(wavelength*0.4))
        sine_troughs_idx, _ = find_peaks(-sine_wave, distance=int(wavelength*0.4))

        # Score: sum of alignment quality
        score = 0.0

        # Score peaks alignment
        for price_peak in peaks_idx:
            if len(sine_peaks_idx) > 0:
                # Find closest sine peak
                distances = np.abs(sine_peaks_idx - price_peak)
                min_dist = np.min(distances)
                # Score decreases with distance (half-wavelength = 0 score)
                peak_score = max(0, 1 - (min_dist / (wavelength / 4)))
                score += peak_score

        # Score troughs alignment
        for price_trough in troughs_idx:
            if len(sine_troughs_idx) > 0:
                # Find closest sine trough
                distances = np.abs(sine_troughs_idx - price_trough)
                min_dist = np.min(distances)
                # Score decreases with distance
                trough_score = max(0, 1 - (min_dist / (wavelength / 4)))
                score += trough_score

        # Normalize by number of extremes
        total_extremes = len(peaks_idx) + len(troughs_idx)
        if total_extremes > 0:
            score = score / total_extremes

        if score > best_score:
            best_score = score
            best_phase = test_phase

    return best_phase, best_score


def create_optimized_bandpass(prices, wavelength, bandwidth_pct=0.10, extend_future=0):
    """
    Create bandpass with phase-optimized alignment

    Process:
    1. Extract wavelet bandpass to get initial phase and amplitude
    2. Optimize phase to align with actual price peaks/troughs
    3. Generate clean sine wave with optimized phase

    Args:
        prices: Price data
        wavelength: Target wavelength
        bandwidth_pct: Bandwidth percentage
        extend_future: Days to project forward

    Returns:
        dict with bandpass, phase, amplitude, and optimization info
    """
    # Step 1: Get initial estimates from wavelet analysis
    log_data = np.log(prices)
    x = np.arange(len(log_data))
    coeffs = np.polyfit(x, log_data, 1)
    trend = np.polyval(coeffs, x)
    detrended = log_data - trend

    # Compute wavelet coefficients
    complex_coeffs, weights = compute_wavelet_coefficients(detrended, wavelength, bandwidth_pct)

    # Extract initial phase and amplitude
    recent_length = min(int(wavelength * 2), len(complex_coeffs))
    recent_coeffs = complex_coeffs[-recent_length:]
    initial_phase = np.angle(np.mean(recent_coeffs))
    initial_amplitude = np.mean(np.abs(recent_coeffs))

    # Step 2: Optimize phase
    optimized_phase, alignment_score = optimize_phase(
        prices, wavelength, initial_phase, initial_amplitude
    )

    # Step 3: Generate PURE sine wave with optimized phase
    # This must be a perfect sine wave for projection
    n = len(prices)
    t = np.arange(n)
    omega = 2 * np.pi / wavelength

    # Generate pure sine wave (not the wavelet output)
    historical_bandpass = np.sin(omega * t + optimized_phase)

    # Project into future
    if extend_future > 0:
        future_t = np.arange(n, n + extend_future)
        future_bandpass = np.sin(omega * future_t + optimized_phase)
        bandpass = np.concatenate([historical_bandpass, future_bandpass])
    else:
        bandpass = historical_bandpass

    # Already normalized (pure sine is ±1)
    bandpass_normalized = bandpass

    phase_change_deg = (optimized_phase - initial_phase) * 180 / np.pi

    return {
        'bandpass_normalized': bandpass_normalized,
        'bandpass_raw': bandpass,
        'phase_radians': optimized_phase,
        'phase_degrees': optimized_phase * 180 / np.pi,
        'amplitude': initial_amplitude,
        'wavelength': wavelength,
        'initial_phase_degrees': initial_phase * 180 / np.pi,
        'phase_adjustment_degrees': phase_change_deg,
        'alignment_score': alignment_score
    }


def main():
    """Test the optimized bandpass on TLT"""
    import sys
    sys.path.append('..')
    sys.path.append('../..')

    from data_manager import DataManager
    import matplotlib.pyplot as plt

    # Load TLT
    dm = DataManager('TLT')
    prices, _ = dm.get_data()

    print(f"\nLoaded {len(prices)} TLT prices")

    # Test with 470d wavelength
    wavelength = 470

    result = create_optimized_bandpass(
        prices,
        wavelength,
        bandwidth_pct=0.10,
        extend_future=700
    )

    print(f"\n{'='*60}")
    print(f"OPTIMIZED BANDPASS RESULTS")
    print(f"{'='*60}")
    print(f"Wavelength: {wavelength}d")
    print(f"Initial phase: {result['initial_phase_degrees']:.1f}°")
    print(f"Optimized phase: {result['phase_degrees']:.1f}°")
    print(f"Phase adjustment: {result['phase_adjustment_degrees']:.1f}°")
    print(f"Alignment score: {result['alignment_score']:.3f}")
    print(f"Amplitude: {result['amplitude']:.6f}")

    # Plot
    recent_prices = prices[-1500:]
    bandpass = result['bandpass_normalized']

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8))
    fig.patch.set_facecolor('black')

    # Plot 1: Prices with bandpass
    ax1.set_facecolor('black')
    ax1.plot(recent_prices, 'gray', alpha=0.5, linewidth=0.5, label='Price')

    price_mean = np.mean(recent_prices)
    price_range = np.max(recent_prices) - np.min(recent_prices)
    scaled_bp = bandpass[-1500:] * (price_range * 0.1) + price_mean

    ax1.plot(scaled_bp, 'yellow', linewidth=2, label='Optimized Bandpass')
    ax1.set_title(f'TLT with Optimized Bandpass ({wavelength}d) - Score: {result["alignment_score"]:.3f}',
                  color='white', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.2, color='gray')
    ax1.tick_params(colors='white')

    # Plot 2: Normalized bandpass
    ax2.set_facecolor('black')
    ax2.plot(bandpass[-1500:], 'yellow', linewidth=2, label='Normalized Bandpass')
    ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax2.set_title(f'Normalized Bandpass (Δφ = {result["phase_adjustment_degrees"]:.1f}°)',
                  color='white', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.2, color='gray')
    ax2.tick_params(colors='white')

    plt.tight_layout()
    plt.savefig('optimized_bandpass_test.png', dpi=120, facecolor='black')
    print(f"\nSaved: optimized_bandpass_test.png")


if __name__ == "__main__":
    main()
