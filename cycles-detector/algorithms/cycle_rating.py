#!/usr/bin/env python3
"""
CYCLE RATING SYSTEM - Based on Sigma-L Classification
======================================================
Implements A/B/C class rating based on:
- Amplitude stationarity
- Frequency stationarity
- Spectral gain/power
- Spectral isolation
"""

import numpy as np
from scipy.signal import find_peaks

def calculate_amplitude_stationarity(bandpass_signal, wavelength):
    """
    Measure how stable the amplitude is over time

    Returns: stationarity_ratio (0-1), where 1 is perfectly stationary
    """
    # Find peaks and troughs
    peaks, _ = find_peaks(bandpass_signal)
    troughs, _ = find_peaks(-bandpass_signal)

    if len(peaks) < 3 or len(troughs) < 3:
        return 0.0

    # Measure peak-to-trough amplitudes
    amplitudes = []
    for i in range(min(len(peaks), len(troughs))):
        if i < len(peaks) and i < len(troughs):
            amp = abs(bandpass_signal[peaks[i]] - bandpass_signal[troughs[i]])
            amplitudes.append(amp)

    if len(amplitudes) < 2:
        return 0.0

    # Calculate coefficient of variation (lower is more stationary)
    mean_amp = np.mean(amplitudes)
    std_amp = np.std(amplitudes)

    if mean_amp == 0:
        return 0.0

    cv = std_amp / mean_amp

    # Convert to stationarity ratio (0-1)
    # CV of 0 = perfect stationarity (ratio=1.0)
    # CV of 0.5+ = poor stationarity (ratio→0)
    stationarity = np.exp(-2 * cv)

    return stationarity


def calculate_frequency_stationarity(bandpass_signal, expected_wavelength):
    """
    Measure how stable the frequency/wavelength is over time

    Returns: stationarity_ratio (0-1), where 1 is perfectly stationary
    """
    # Find zero crossings to measure actual wavelengths
    zero_crossings = np.where(np.diff(np.sign(bandpass_signal)))[0]

    if len(zero_crossings) < 4:
        return 0.0

    # Measure wavelengths (full cycle = 2 zero crossings)
    wavelengths = []
    for i in range(0, len(zero_crossings) - 2, 2):
        wl = zero_crossings[i+2] - zero_crossings[i]
        wavelengths.append(wl)

    if len(wavelengths) < 2:
        return 0.0

    # Calculate deviation from expected wavelength
    wavelengths = np.array(wavelengths)
    mean_wl = np.mean(wavelengths)
    std_wl = np.std(wavelengths)

    # Coefficient of variation
    if mean_wl == 0:
        return 0.0

    cv = std_wl / mean_wl

    # Also penalize if mean differs significantly from expected
    wavelength_error = abs(mean_wl - expected_wavelength) / expected_wavelength

    # Combine CV and wavelength error
    # CV of 0 and error of 0 = perfect (ratio=1.0)
    stationarity = np.exp(-2 * cv - wavelength_error)

    return stationarity


def calculate_spectral_isolation(spectrum, peak_idx, wavelengths):
    """
    Measure how isolated the peak is from other peaks (spectral spacing)

    Returns: isolation_ratio (0-1), where 1 is perfectly isolated
    """
    if peak_idx < 0 or peak_idx >= len(spectrum):
        return 0.0

    peak_power = spectrum[peak_idx]

    # Find all other peaks in spectrum
    all_peaks, properties = find_peaks(spectrum, height=0.1, distance=3)

    if len(all_peaks) == 0:
        return 0.0

    # Remove the target peak from list
    other_peaks = all_peaks[all_peaks != peak_idx]

    if len(other_peaks) == 0:
        # No other peaks - perfectly isolated
        return 1.0

    # Find closest peak
    distances = np.abs(other_peaks - peak_idx)
    closest_idx = other_peaks[np.argmin(distances)]
    min_distance = np.min(distances)

    # Power ratio: how much stronger is our peak vs nearest peak
    nearest_power = spectrum[closest_idx]
    power_ratio = peak_power / (nearest_power + 1e-10)

    # Distance in terms of wavelengths
    target_wl = wavelengths[peak_idx]
    nearest_wl = wavelengths[closest_idx]
    wl_separation = abs(target_wl - nearest_wl) / target_wl

    # Isolation score combines distance and power dominance
    # Good: large separation AND high power ratio
    isolation = min(1.0, (wl_separation * 0.5 + np.tanh(power_ratio - 1) * 0.5))

    return max(0.0, isolation)


def calculate_signal_to_noise(spectrum, peak_idx, window=10):
    """
    Calculate signal-to-noise ratio around the peak

    Returns: SNR value (higher is better)
    """
    if peak_idx < 0 or peak_idx >= len(spectrum):
        return 0.0

    peak_power = spectrum[peak_idx]

    # Define noise region (away from peak)
    start_noise = max(0, peak_idx - window - 20)
    end_noise = max(0, peak_idx - window)

    start_noise2 = min(len(spectrum), peak_idx + window)
    end_noise2 = min(len(spectrum), peak_idx + window + 20)

    # Calculate noise level
    noise_values = []
    if end_noise > start_noise:
        noise_values.extend(spectrum[start_noise:end_noise])
    if end_noise2 > start_noise2:
        noise_values.extend(spectrum[start_noise2:end_noise2])

    if len(noise_values) == 0:
        return 0.0

    noise_level = np.mean(noise_values)

    if noise_level == 0:
        return 100.0  # Perfect SNR

    snr = peak_power / noise_level

    return snr


def rate_cycle(bandpass_signal, wavelength, spectrum, peak_idx, wavelengths):
    """
    Rate a detected cycle using Sigma-L classification system

    Args:
        bandpass_signal: The bandpass filtered signal
        wavelength: Expected wavelength in trading days
        spectrum: Power spectrum array
        peak_idx: Index of the peak in spectrum
        wavelengths: Array of wavelengths corresponding to spectrum

    Returns:
        dict with:
            - class: 'A', 'B', 'C', or 'D' (D for poor signals)
            - score: 0-100 numerical score
            - amp_stationarity: 0-1
            - freq_stationarity: 0-1
            - spectral_isolation: 0-1
            - snr: signal-to-noise ratio
            - gain_rank: relative power ranking
    """

    # Calculate individual metrics
    amp_stat = calculate_amplitude_stationarity(bandpass_signal, wavelength)
    freq_stat = calculate_frequency_stationarity(bandpass_signal, wavelength)
    isolation = calculate_spectral_isolation(spectrum, peak_idx, wavelengths)
    snr = calculate_signal_to_noise(spectrum, peak_idx)

    # Determine gain rank (is this the strongest peak?)
    sorted_spectrum = np.sort(spectrum)[::-1]
    peak_power = spectrum[peak_idx]

    if peak_power >= sorted_spectrum[0] * 0.95:  # Within 5% of max
        gain_rank = 1
    elif len(sorted_spectrum) > 1 and peak_power >= sorted_spectrum[1] * 0.95:
        gain_rank = 2
    else:
        gain_rank = 3

    # Classification logic based on Sigma-L criteria

    # Class A: Highly stationary (>0.8) for majority, max gain, clear spacing
    if (amp_stat > 0.8 and freq_stat > 0.8 and
        gain_rank == 1 and isolation > 0.7 and snr > 5.0):
        signal_class = 'A'
        base_score = 90

    # Class B: Highly stationary (>0.7) for at least half, max or 2nd gain, clear spacing
    elif (amp_stat > 0.7 and freq_stat > 0.7 and
          gain_rank <= 2 and isolation > 0.6 and snr > 3.0):
        signal_class = 'B'
        base_score = 75

    # Class C: Moderately stationary (>0.6), max or 2nd gain
    elif (amp_stat > 0.6 and freq_stat > 0.6 and
          gain_rank <= 2 and snr > 2.0):
        signal_class = 'C'
        base_score = 60

    # Class D: Poor signal
    else:
        signal_class = 'D'
        base_score = 40

    # Calculate numerical score (0-100)
    score = base_score + (amp_stat * 3) + (freq_stat * 3) + (isolation * 2) + (min(snr, 10) * 0.5)
    score = min(100, max(0, score))

    return {
        'class': signal_class,
        'score': round(score, 1),
        'amp_stationarity': round(amp_stat, 3),
        'freq_stationarity': round(freq_stat, 3),
        'spectral_isolation': round(isolation, 3),
        'snr': round(snr, 2),
        'gain_rank': gain_rank,
        'emoji': get_rating_emoji(signal_class)
    }


def get_rating_emoji(signal_class):
    """Get emoji for signal class"""
    emoji_map = {
        'A': '🔥',  # Fire - wow signal
        'B': '👌',  # OK hand - excellent
        'C': '👍',  # Thumbs up - good
        'D': '⚠️'   # Warning - caution
    }
    return emoji_map.get(signal_class, '❓')


def get_rating_description(signal_class):
    """Get description for signal class"""
    descriptions = {
        'A': 'WOW! Highly stationary, beacon-like quality',
        'B': 'Excellent - Clear and tradeable signal',
        'C': 'Good - Moderate stationarity, use with caution',
        'D': 'Weak - High modulation, risky to trade'
    }
    return descriptions.get(signal_class, 'Unknown')
