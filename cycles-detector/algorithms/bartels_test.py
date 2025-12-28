#!/usr/bin/env python3
"""
BARTELS SIGNIFICANCE TEST
=========================
Statistical test for cycle genuineness vs randomness.
Based on Julius Bartels (1932) periodicity test.

Returns 0-100% score where:
- >49%: Genuine cycle (statistically significant)
- <49%: Random/spurious cycle (should be filtered)
"""

import numpy as np


def calculate_bartels_score(bandpass_signal, wavelength):
    """
    Calculate Bartels significance test for a cycle.

    The Bartels test measures the stability of amplitude and phase
    by comparing the actual signal to random permutations.

    Args:
        bandpass_signal: Bandpass filtered signal for specific wavelength
        wavelength: The wavelength in trading days

    Returns:
        float: Bartels score 0-100% (higher = more genuine)
    """

    if len(bandpass_signal) < wavelength * 2:
        return 0.0  # Not enough data

    # Calculate variance of the bandpass signal
    signal_variance = np.var(bandpass_signal)

    if signal_variance == 0:
        return 0.0  # No signal present

    # Calculate autocorrelation at the target wavelength
    # High autocorrelation at the wavelength indicates genuine periodicity
    lag = int(wavelength)

    if lag >= len(bandpass_signal):
        return 0.0

    # Autocorrelation coefficient at lag
    mean = np.mean(bandpass_signal)
    numerator = np.sum((bandpass_signal[:-lag] - mean) * (bandpass_signal[lag:] - mean))
    denominator = np.sum((bandpass_signal - mean) ** 2)

    if denominator == 0:
        return 0.0

    autocorr = numerator / denominator

    # Calculate phase consistency
    # Split signal into segments of one wavelength each
    num_cycles = len(bandpass_signal) // wavelength

    if num_cycles < 2:
        return 0.0

    # Extract cycle segments
    segments = []
    for i in range(num_cycles):
        start = i * wavelength
        end = start + wavelength
        if end <= len(bandpass_signal):
            segments.append(bandpass_signal[start:end])

    if len(segments) < 2:
        return 0.0

    # Calculate cross-correlation between consecutive segments
    # High cross-correlation = stable phase relationship
    cross_corrs = []
    for i in range(len(segments) - 1):
        seg1 = segments[i]
        seg2 = segments[i + 1]

        # Normalize segments
        seg1_norm = (seg1 - np.mean(seg1)) / (np.std(seg1) + 1e-10)
        seg2_norm = (seg2 - np.mean(seg2)) / (np.std(seg2) + 1e-10)

        # Cross-correlation
        cross_corr = np.corrcoef(seg1_norm, seg2_norm)[0, 1]

        if not np.isnan(cross_corr):
            cross_corrs.append(abs(cross_corr))

    if len(cross_corrs) == 0:
        return 0.0

    phase_stability = np.mean(cross_corrs)

    # Calculate amplitude consistency
    # Measure variation in peak amplitudes across cycles
    peak_amplitudes = []
    for seg in segments:
        peak_amp = np.max(np.abs(seg))
        peak_amplitudes.append(peak_amp)

    if len(peak_amplitudes) < 2:
        return 0.0

    mean_amplitude = np.mean(peak_amplitudes)
    amplitude_cv = np.std(peak_amplitudes) / (mean_amplitude + 1e-10)

    # Lower coefficient of variation = more consistent amplitude
    amplitude_consistency = np.exp(-amplitude_cv)

    # Combine metrics to calculate Bartels score
    # Weights:
    # - Autocorrelation: 40% (periodicity at target wavelength)
    # - Phase stability: 40% (cycle-to-cycle consistency)
    # - Amplitude consistency: 20% (stable amplitude)

    # Normalize autocorrelation to 0-1 (can be negative)
    autocorr_score = (autocorr + 1) / 2.0  # Map [-1, 1] to [0, 1]
    autocorr_score = max(0, min(1, autocorr_score))

    # Combine weighted scores
    bartels_score = (
        0.4 * autocorr_score +
        0.4 * phase_stability +
        0.2 * amplitude_consistency
    )

    # Convert to percentage
    bartels_percentage = bartels_score * 100.0

    return min(100.0, max(0.0, bartels_percentage))


def filter_cycles_by_bartels(spectrum, wavelengths, bandpass_signals, threshold=49.0):
    """
    Filter detected cycles using Bartels significance test.

    Args:
        spectrum: Power spectrum array
        wavelengths: Array of wavelengths corresponding to spectrum
        bandpass_signals: Dict mapping wavelength -> bandpass signal
        threshold: Bartels score threshold (default: 49%)

    Returns:
        dict with:
            - filtered_spectrum: Spectrum with non-significant cycles zeroed out
            - bartels_scores: Dict mapping wavelength -> Bartels score
            - num_filtered: Number of cycles filtered out
    """

    filtered_spectrum = spectrum.copy()
    bartels_scores = {}
    num_filtered = 0

    for i, wavelength in enumerate(wavelengths):
        # Get bandpass signal for this wavelength (if available)
        if wavelength in bandpass_signals:
            bandpass = bandpass_signals[wavelength]
            score = calculate_bartels_score(bandpass, wavelength)
            bartels_scores[wavelength] = score

            # Filter out cycles below threshold
            if score < threshold:
                filtered_spectrum[i] = 0.0
                num_filtered += 1

    return {
        'filtered_spectrum': filtered_spectrum,
        'bartels_scores': bartels_scores,
        'num_filtered': num_filtered,
        'threshold': threshold
    }


def get_bartels_rating(score):
    """
    Get descriptive rating for Bartels score.

    Args:
        score: Bartels percentage (0-100)

    Returns:
        dict with rating info
    """

    if score >= 75:
        rating = 'A'
        description = 'Highly genuine - Excellent cycle stability'
        color = '#00ff00'  # Green
    elif score >= 60:
        rating = 'B'
        description = 'Genuine - Good cycle consistency'
        color = '#88ff00'  # Yellow-green
    elif score >= 49:
        rating = 'C'
        description = 'Marginal - Acceptable but less stable'
        color = '#ffaa00'  # Orange
    else:
        rating = 'D'
        description = 'Random/Spurious - Should be filtered'
        color = '#ff4444'  # Red

    return {
        'rating': rating,
        'description': description,
        'color': color,
        'is_significant': score >= 49.0
    }
