#!/usr/bin/env python3
"""
Weighted Morlet Wavelet Bandpass Algorithm
==========================================
Based on SIGMA-L documentation (Understanding Charts Part 2):

"The yellow band-pass on price is the result of a weighted by amplitude
band-pass region of the time frequency analysis, related to the detected
area of interest... derived from the result of complex morlet wavelet convolution"

This produces a pure sine wave that can be projected into the future.
"""

import numpy as np


def create_high_q_morlet(freq, length):
    """
    Create high-Q Morlet wavelet (same as heatmap_algo.py)

    Args:
        freq: Frequency (1/wavelength)
        length: Wavelet length in samples

    Returns:
        Complex Morlet wavelet array
    """
    Q = 15.0 + 50.0 * freq
    sigma = Q / (2.0 * np.pi * freq)

    t = np.arange(length) - length/2.0
    envelope = np.exp(-t**2 / (2.0 * sigma**2))
    carrier = np.exp(1j * 2.0 * np.pi * freq * t)
    wavelet = envelope * carrier

    # Normalize
    norm = np.sqrt(np.sum(np.abs(wavelet)**2))
    wavelet /= norm

    return wavelet


def compute_wavelet_coefficients(data, center_wavelength, bandwidth_pct=0.10):
    """
    Compute weighted Morlet wavelet coefficients for a wavelength band

    Uses sliding window approach similar to heatmap_algo.py compute_power()

    Args:
        data: Price data (should be log-transformed and detrended)
        center_wavelength: Center wavelength in days
        bandwidth_pct: Bandwidth as percentage of center wavelength (default 10%)

    Returns:
        complex_coeffs: Complex wavelet coefficients at each time point
        weights: Amplitude weights used for averaging
    """
    n = len(data)

    # Define frequency band
    bandwidth = center_wavelength * bandwidth_pct
    min_wl = center_wavelength - bandwidth/2
    max_wl = center_wavelength + bandwidth/2

    # Sample 5 frequencies within the band
    num_freqs = 5
    wavelengths = np.linspace(min_wl, max_wl, num_freqs)

    # Storage for coefficients at each frequency
    all_coeffs = np.zeros((num_freqs, n), dtype=complex)
    all_amplitudes = np.zeros(num_freqs)

    # Compute wavelet transform for each frequency
    for i, wl in enumerate(wavelengths):
        freq = 1.0 / wl

        # Wavelet length: 4-8 cycles (same as heatmap)
        cycles = min(8, max(4, n // int(wl)))
        wlen = min(n, int(wl * cycles))

        # Create wavelet
        wavelet = create_high_q_morlet(freq, wlen)

        # Sliding window convolution - compute at every point for full coverage
        coeffs = np.zeros(n, dtype=complex)

        for center in range(n):
            start_idx = center - wlen//2
            end_idx = start_idx + wlen

            # Handle edges by using available data
            if start_idx < 0:
                # Pad beginning
                wavelet_start = -start_idx
                data_start = 0
                signal_segment = data[data_start:min(end_idx, n)]
                wavelet_segment = wavelet[wavelet_start:wavelet_start+len(signal_segment)]
            elif end_idx > n:
                # Pad end
                wavelet_end = wlen - (end_idx - n)
                data_end = n
                signal_segment = data[max(start_idx, 0):data_end]
                wavelet_segment = wavelet[:len(signal_segment)]
            else:
                # Normal case
                signal_segment = data[start_idx:end_idx]
                wavelet_segment = wavelet

            # Complex wavelet convolution
            if len(signal_segment) > 0 and len(wavelet_segment) > 0:
                conv = np.sum(signal_segment * np.conj(wavelet_segment))
                coeffs[center] = conv

        all_coeffs[i, :] = coeffs

        # Compute average amplitude for this frequency (for weighting)
        all_amplitudes[i] = np.mean(np.abs(coeffs))

    # Weight by amplitude - frequencies with larger amplitude get more weight
    if np.sum(all_amplitudes) > 0:
        weights = all_amplitudes / np.sum(all_amplitudes)
    else:
        weights = np.ones(num_freqs) / num_freqs

    # Weighted average of complex coefficients
    weighted_coeffs = np.zeros(n, dtype=complex)
    for i in range(num_freqs):
        weighted_coeffs += weights[i] * all_coeffs[i, :]

    return weighted_coeffs, weights


def extract_bandpass_sine_wave(data, wavelength, bandwidth_pct=0.10, extend_future=0):
    """
    Extract bandpass sine wave using weighted Morlet wavelet coefficients

    This is the SIGMA-L approach: weighted average of wavelet outputs.

    Args:
        data: Raw price data
        wavelength: Target wavelength in days
        bandwidth_pct: Bandwidth percentage (default 10%)
        extend_future: Number of future points to project

    Returns:
        bandpass: Bandpass sine wave (historical + future projection)
        phase: Extracted phase in radians
        amplitude: Extracted amplitude
    """
    # Preprocess: log-transform and detrend
    log_data = np.log(data)

    # Linear detrend
    x = np.arange(len(log_data))
    coeffs = np.polyfit(x, log_data, 1)
    trend = np.polyval(coeffs, x)
    detrended = log_data - trend

    # Compute complex wavelet coefficients
    complex_coeffs, weights = compute_wavelet_coefficients(detrended, wavelength, bandwidth_pct)

    # Extract real part - this is the bandpass sine wave
    historical_bandpass = np.real(complex_coeffs)

    # Extract phase and amplitude from recent coefficients (last cycle)
    recent_length = min(int(wavelength * 2), len(complex_coeffs))
    recent_coeffs = complex_coeffs[-recent_length:]

    # Average phase from recent coefficients
    avg_phase = np.angle(np.mean(recent_coeffs))

    # Average amplitude from recent coefficients
    avg_amplitude = np.mean(np.abs(recent_coeffs))

    # Project into future using extracted phase and amplitude
    if extend_future > 0:
        n = len(data)
        future_indices = np.arange(n, n + extend_future)
        omega = 2 * np.pi / wavelength

        # Continue the sine wave with extracted phase
        future_bandpass = avg_amplitude * np.sin(omega * future_indices + avg_phase)

        # Combine historical and future
        bandpass = np.concatenate([historical_bandpass, future_bandpass])
    else:
        bandpass = historical_bandpass

    return bandpass, avg_phase, avg_amplitude


def create_wavelet_bandpass_filter(prices, wavelength, bandwidth_pct=0.10, extend_future=0):
    """
    Main function: Create bandpass filter using weighted Morlet wavelets

    Args:
        prices: Price data array
        wavelength: Target wavelength in days
        bandwidth_pct: Bandwidth as % of wavelength
        extend_future: Number of future days to project

    Returns:
        dict with:
            - bandpass_normalized: Normalized bandpass (±1 range)
            - bandpass_raw: Raw bandpass from wavelets
            - phase_radians: Extracted phase
            - phase_degrees: Extracted phase in degrees
            - amplitude: Extracted amplitude
            - weights: Frequency weights used
    """
    bandpass, phase, amplitude = extract_bandpass_sine_wave(
        prices, wavelength, bandwidth_pct, extend_future
    )

    # Normalize to ±1 range for consistency
    if amplitude > 0:
        bandpass_normalized = bandpass / amplitude
    else:
        bandpass_normalized = bandpass

    return {
        'bandpass_normalized': bandpass_normalized,
        'bandpass_raw': bandpass,
        'phase_radians': phase,
        'phase_degrees': phase * 180 / np.pi,
        'amplitude': amplitude,
        'wavelength': wavelength
    }


def main():
    """
    Test the wavelet bandpass algorithm
    """
    import matplotlib.pyplot as plt

    # Generate test data: sine wave + noise + trend
    n = 2000
    t = np.arange(n)
    true_wavelength = 350
    true_phase = np.pi / 4

    # True signal
    omega = 2 * np.pi / true_wavelength
    true_signal = np.sin(omega * t + true_phase)

    # Add trend and noise
    trend = 0.0005 * t
    noise = 0.3 * np.random.randn(n)

    # Generate prices
    log_prices = trend + true_signal + noise
    prices = np.exp(log_prices) * 100  # Start at $100

    # Apply wavelet bandpass
    result = create_wavelet_bandpass_filter(prices, 350, bandwidth_pct=0.10, extend_future=700)

    print("\n" + "="*60)
    print("WAVELET BANDPASS FILTER TEST")
    print("="*60)
    print(f"True wavelength: {true_wavelength}d")
    print(f"True phase: {true_phase * 180 / np.pi:.1f}°")
    print(f"\nExtracted phase: {result['phase_degrees']:.1f}°")
    print(f"Extracted amplitude: {result['amplitude']:.6f}")
    print(f"Wavelength used: {result['wavelength']:.0f}d")

    # Plot
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 8))

    # Plot 1: Prices with bandpass
    ax1.plot(t, prices, 'gray', alpha=0.5, linewidth=0.5, label='Prices')

    # Scale bandpass to price range
    price_mean = np.mean(prices)
    price_range = np.max(prices) - np.min(prices)
    scaled_bandpass = result['bandpass_normalized'] * (price_range * 0.1) + price_mean

    historical_len = len(prices)
    total_len = len(scaled_bandpass)
    t_full = np.arange(total_len)

    ax1.plot(t_full[:historical_len], scaled_bandpass[:historical_len],
             'cyan', linewidth=2, label='Wavelet Bandpass (Historical)')
    ax1.plot(t_full[historical_len:], scaled_bandpass[historical_len:],
             'yellow', linewidth=2, linestyle='--', label='Projection')

    ax1.axvline(historical_len, color='red', linestyle='--', alpha=0.5, label='Now')
    ax1.set_title('Wavelet Bandpass on Prices', color='white', fontsize=14)
    ax1.set_xlabel('Time (days)', color='white')
    ax1.set_ylabel('Price', color='white')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Normalized bandpass
    ax2.plot(t_full[:historical_len], result['bandpass_normalized'][:historical_len],
             'cyan', linewidth=2, label='Wavelet Bandpass')
    ax2.plot(t_full[historical_len:], result['bandpass_normalized'][historical_len:],
             'yellow', linewidth=2, linestyle='--', label='Projection')
    ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)
    ax2.axvline(historical_len, color='red', linestyle='--', alpha=0.5)
    ax2.set_title(f'Normalized Bandpass (Phase: {result["phase_degrees"]:.1f}°)',
                  color='white', fontsize=14)
    ax2.set_xlabel('Time (days)', color='white')
    ax2.set_ylabel('Normalized Amplitude', color='white')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('wavelet_bandpass_test.png', dpi=120, facecolor='black')
    print("\nSaved: wavelet_bandpass_test.png")


if __name__ == "__main__":
    main()
