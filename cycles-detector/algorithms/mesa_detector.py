#!/usr/bin/env python3
"""
MESA CYCLE DETECTOR
===================
Maximum Entropy Spectral Analysis (MESA) for cycle detection
Based on John Ehlers' adaptive cycle detection methodology

MESA adaptively detects dominant market cycles by analyzing
the power spectrum using maximum entropy methods.
"""

import numpy as np
from scipy.signal import find_peaks


def mesa_cycle_detector(prices, min_wavelength=10, max_wavelength=500,
                        window_size=None, num_peaks=10):
    """
    Detect cycles using MESA (Maximum Entropy Spectral Analysis)

    Args:
        prices: Price data array
        min_wavelength: Minimum cycle period to detect (trading days)
        max_wavelength: Maximum cycle period to detect (trading days)
        window_size: Analysis window size (default: length of prices)
        num_peaks: Maximum number of peaks to return

    Returns:
        Dictionary with:
            - wavelengths: Array of detected wavelengths
            - spectrum: Power spectrum values
            - peaks: Indices of detected peaks
    """

    # Ensure prices is a 1D numpy array
    prices = np.asarray(prices).flatten()

    if window_size is None:
        window_size = len(prices)

    # Use most recent data if window smaller than full dataset
    if window_size < len(prices):
        prices = prices[-window_size:]

    # Step 1: Detrend the price data
    log_prices = np.log(prices)
    x = np.arange(len(log_prices))
    coeffs = np.polyfit(x, log_prices, 1)
    trend = np.polyval(coeffs, x)
    detrended = log_prices - trend

    # Step 2: Calculate MESA power spectrum
    # Using autocorrelation-based method (Burg's method approximation)
    n = len(detrended)

    # Calculate autocorrelation
    autocorr = np.correlate(detrended, detrended, mode='full')
    autocorr = autocorr[n-1:]  # Keep only positive lags
    autocorr = autocorr / autocorr[0]  # Normalize

    # Step 3: Calculate power spectrum via FFT of autocorrelation
    # This gives us frequency components
    spectrum_fft = np.fft.fft(autocorr, n=n*2)
    power_spectrum = np.abs(spectrum_fft[:n])

    # Step 4: Convert frequency bins to wavelengths
    # Wavelength = 1 / frequency
    freq_bins = np.fft.fftfreq(n*2, d=1.0)[:n]
    freq_bins[0] = 1e-10  # Avoid division by zero
    wavelengths_all = 1.0 / np.abs(freq_bins)

    # Step 5: Filter to valid wavelength range
    valid_mask = (wavelengths_all >= min_wavelength) & (wavelengths_all <= max_wavelength)
    wavelengths = wavelengths_all[valid_mask]
    spectrum = power_spectrum[valid_mask]

    if len(spectrum) == 0:
        return {
            'wavelengths': np.array([]),
            'spectrum': np.array([]),
            'peaks': np.array([])
        }

    # Step 6: Find peaks in power spectrum
    # Use prominence and distance to find significant cycles
    min_distance = 3  # Minimum separation between peaks (reduced from 5)

    # Much more sensitive threshold - detect cycles down to 2% of max power
    # This matches what other scanners do
    min_prominence = np.max(spectrum) * 0.02  # At least 2% of max power

    # REMOVED height filter to show ALL cycles, even weak ones
    peaks_idx, properties = find_peaks(
        spectrum,
        distance=min_distance,
        prominence=min_prominence
        # height filter removed - show all cycles regardless of strength
    )

    # Step 7: Sort peaks by power (descending) and limit to num_peaks
    if len(peaks_idx) > 0:
        peak_powers = spectrum[peaks_idx]
        sorted_indices = np.argsort(peak_powers)[::-1]  # Descending order
        peaks_idx = peaks_idx[sorted_indices[:num_peaks]]

    return {
        'wavelengths': wavelengths,
        'spectrum': spectrum,
        'peaks': peaks_idx
    }


def calculate_mesa_significance(prices, wavelength, bandwidth_pct=0.10):
    """
    Calculate significance score for a MESA-detected cycle

    Uses phase consistency and amplitude stability to validate cycle

    Args:
        prices: Price data
        wavelength: Detected wavelength
        bandwidth_pct: Bandwidth for bandpass filter

    Returns:
        float: Significance score 0-100%
    """

    # Ensure prices is a 1D numpy array
    prices = np.asarray(prices).flatten()

    if len(prices) < wavelength * 2:
        return 0.0

    # Detrend
    log_prices = np.log(prices)
    x = np.arange(len(log_prices))
    coeffs = np.polyfit(x, log_prices, 1)
    trend = np.polyval(coeffs, x)
    detrended = log_prices - trend

    # Bandpass filter around target wavelength
    n = len(detrended)
    freq = np.fft.fftfreq(n)
    target_freq = 1.0 / wavelength
    bandwidth = target_freq * bandwidth_pct

    # Create bandpass filter
    H = np.zeros(len(freq))
    for i, f in enumerate(freq):
        if abs(abs(f) - target_freq) < bandwidth:
            H[i] = 1.0

    # Apply filter
    fft_data = np.fft.fft(detrended)
    filtered_fft = fft_data * H
    filtered_signal = np.real(np.fft.ifft(filtered_fft))

    # Calculate phase consistency across cycles
    num_cycles = len(filtered_signal) // wavelength

    if num_cycles < 2:
        return 0.0

    # Extract cycle segments
    segments = []
    for i in range(num_cycles):
        start = i * wavelength
        end = start + wavelength
        if end <= len(filtered_signal):
            segments.append(filtered_signal[start:end])

    if len(segments) < 2:
        return 0.0

    # Calculate cross-correlation between segments
    cross_corrs = []
    for i in range(len(segments) - 1):
        seg1 = segments[i]
        seg2 = segments[i + 1]

        # Normalize
        seg1_norm = (seg1 - np.mean(seg1)) / (np.std(seg1) + 1e-10)
        seg2_norm = (seg2 - np.mean(seg2)) / (np.std(seg2) + 1e-10)

        # Cross-correlation
        cross_corr = np.corrcoef(seg1_norm, seg2_norm)[0, 1]

        if not np.isnan(cross_corr):
            cross_corrs.append(abs(cross_corr))

    if len(cross_corrs) == 0:
        return 0.0

    # Phase consistency score
    phase_consistency = np.mean(cross_corrs)

    # Calculate autocorrelation at wavelength
    mean = np.mean(filtered_signal)
    lag = int(wavelength)

    if lag >= len(filtered_signal):
        return 0.0

    numerator = np.sum((filtered_signal[:-lag] - mean) * (filtered_signal[lag:] - mean))
    denominator = np.sum((filtered_signal - mean) ** 2)

    if denominator == 0:
        return 0.0

    autocorr = numerator / denominator
    autocorr_score = (autocorr + 1) / 2.0  # Map [-1, 1] to [0, 1]
    autocorr_score = max(0, min(1, autocorr_score))

    # Combine scores
    significance = (0.6 * phase_consistency + 0.4 * autocorr_score) * 100

    return min(100.0, max(0.0, significance))


def get_mesa_rating(significance_score):
    """
    Get rating for MESA significance score

    Args:
        significance_score: Significance percentage (0-100)

    Returns:
        dict with rating info
    """

    if significance_score >= 75:
        rating = 'A'
        description = 'Highly significant - Strong dominant cycle'
        color = '#00ff00'  # Green
    elif significance_score >= 60:
        rating = 'B'
        description = 'Significant - Good cycle strength'
        color = '#88ff00'  # Yellow-green
    elif significance_score >= 45:
        rating = 'C'
        description = 'Moderate - Detectable cycle'
        color = '#ffaa00'  # Orange
    else:
        rating = 'D'
        description = 'Weak - Low significance'
        color = '#ff4444'  # Red

    return {
        'rating': rating,
        'description': description,
        'color': color,
        'is_significant': significance_score >= 45.0
    }
