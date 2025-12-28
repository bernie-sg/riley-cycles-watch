#!/usr/bin/env python3
"""
Bandpass Filter with Phase Extraction - V10 IMPROVED
Aligns sine wave to ACTUAL price turning points, not filtered signal
"""
import numpy as np
from scipy.signal import hilbert, butter, filtfilt, find_peaks


def create_pure_sine_bandpass(prices, wavelength, bandwidth_pct=0.10, extend_future=700,
                                method='actual_price_peaks', align_to='trough'):
    """
    Generate sine wave bandpass aligned to price data

    Args:
        prices: Price data array
        wavelength: Cycle period in trading days
        bandwidth_pct: Bandwidth for filtering (default 10%)
        extend_future: Number of days to project forward
        method: 'actual_price_peaks' (new, recommended) or 'filtered_signal' (old V9)
        align_to: 'trough' (default, more predictable) or 'peak' (tops) or 'auto' (most recent)

    Returns:
        Dictionary with bandpass and metadata
    """

    if method == 'filtered_signal':
        # OLD V9 METHOD - kept for comparison
        return _create_bandpass_v9_method(prices, wavelength, bandwidth_pct, extend_future)
    elif method == 'actual_price_peaks':
        # NEW V10 METHOD - aligns to actual price turning points
        return _create_bandpass_actual_peaks(prices, wavelength, bandwidth_pct, extend_future, align_to)
    elif method == 'hilbert_phase':
        # ALTERNATIVE METHOD - uses Hilbert transform phase extraction
        return _create_bandpass_hilbert_phase(prices, wavelength, bandwidth_pct, extend_future, align_to)
    else:
        raise ValueError(f"Unknown method: {method}")


def _create_bandpass_v9_method(prices, wavelength, bandwidth_pct, extend_future):
    """
    OLD V9 METHOD - aligns to filtered signal lows (has phase shift issues)
    Kept for comparison purposes
    """
    # Detrend price data
    min_price = np.min(prices)
    if min_price <= 0:
        prices_positive = prices - min_price + 1.0
    else:
        prices_positive = prices

    log_prices = np.log(prices_positive)
    x = np.arange(len(log_prices))
    coeffs = np.polyfit(x, log_prices, 1)
    trend = np.polyval(coeffs, x)
    detrended = log_prices - trend

    # Create bandpass filter in frequency domain
    n = len(detrended)
    freq = np.fft.fftfreq(n)

    target_freq = 1.0 / wavelength
    bandwidth = target_freq * bandwidth_pct

    # Bandpass filter: keep frequencies near target
    H = np.zeros(len(freq))
    for i, f in enumerate(freq):
        if abs(abs(f) - target_freq) < bandwidth:
            H[i] = 1.0

    # Apply filter
    fft_data = np.fft.fft(detrended)
    filtered_fft = fft_data * H
    filtered_signal = np.real(np.fft.ifft(filtered_fft))

    # Find cycle lows in filtered signal
    search_window = min(len(filtered_signal), int(wavelength * 2.5))
    recent_filtered = filtered_signal[-search_window:]

    lows_idx, _ = find_peaks(-recent_filtered, distance=int(wavelength * 0.40))

    if len(lows_idx) > 0:
        t_low = len(filtered_signal) - search_window + lows_idx[-1]
    else:
        t_low = len(filtered_signal) - search_window + np.argmin(recent_filtered)

    amplitude = np.std(filtered_signal)
    if amplitude < 1e-10:
        amplitude = 1.0

    # Generate sine wave
    total_length = len(prices) + extend_future
    t = np.arange(total_length)
    omega = 2 * np.pi / wavelength

    phase_offset = -np.pi / 2 - omega * t_low
    sine_wave = amplitude * np.sin(omega * t + phase_offset)

    if amplitude > 1e-10:
        sine_wave_normalized = sine_wave / amplitude
    else:
        sine_wave_normalized = sine_wave

    phase_at_end = omega * (len(prices) - 1) + phase_offset
    phase_degrees = (phase_at_end * 180 / np.pi) % 360

    return {
        'bandpass_normalized': sine_wave_normalized,
        'method': 'V9_filtered_signal_lows',
        'phase_degrees': float(phase_degrees),
        'amplitude': float(amplitude),
        'wavelength': wavelength,
        't_low_index': int(t_low)
    }


def _create_bandpass_actual_peaks(prices, wavelength, bandwidth_pct, extend_future, align_to='trough'):
    """
    NEW V10 METHOD - aligns to ACTUAL price turning points

    This method:
    1. Detrends prices using polynomial fit
    2. Finds ACTUAL price peaks/troughs in detrended data
    3. Validates peaks against expected wavelength
    4. Aligns sine wave to the most recent valid turning point

    Args:
        align_to: 'trough' (default), 'peak', or 'auto' (most recent)
    """

    # Step 1: Detrend using robust polynomial (removes long-term trend)
    x = np.arange(len(prices))

    # Use 3rd degree polynomial for better trend removal
    try:
        coeffs = np.polyfit(x, prices, 3)
        trend = np.polyval(coeffs, x)
        detrended = prices - trend
    except:
        # Fallback to mean
        detrended = prices - np.mean(prices)

    # Step 2: Find ACTUAL price turning points in detrended data
    # Look in last 3 wavelengths for recent turning points
    search_window = min(len(detrended), int(wavelength * 3.0))
    recent_detrended = detrended[-search_window:]

    # Find peaks (highs) with appropriate distance
    min_peak_distance = int(wavelength * 0.4)  # At least 40% of wavelength apart

    peaks_idx, peak_props = find_peaks(
        recent_detrended,
        distance=min_peak_distance,
        prominence=np.std(recent_detrended) * 0.2  # Must be prominent
    )

    troughs_idx, trough_props = find_peaks(
        -recent_detrended,
        distance=min_peak_distance,
        prominence=np.std(recent_detrended) * 0.2
    )

    # Step 3: Combine peaks and troughs, sorted by position
    turning_points = []
    for idx in peaks_idx:
        turning_points.append((idx, 'peak'))
    for idx in troughs_idx:
        turning_points.append((idx, 'trough'))

    turning_points.sort(key=lambda x: x[0])

    # Step 4: Find the turning point based on align_to preference
    # CRITICAL: Exclude turning points too close to end (still developing)
    # Use most PROMINENT turning point for better alignment

    # Minimum distance from end to ensure turning point is confirmed
    min_bars_from_end = int(wavelength * 0.25)  # At least 25% of wavelength from end

    # Filter out turning points too close to end
    def filter_recent_turning_points(indices, prominences):
        """Keep only turning points that are far enough from the end"""
        if len(indices) == 0:
            return indices, prominences

        # Calculate absolute indices
        abs_indices = [len(detrended) - search_window + idx for idx in indices]
        bars_from_end = [len(detrended) - 1 - abs_idx for abs_idx in abs_indices]

        # Keep only those far enough from end
        valid_mask = np.array(bars_from_end) >= min_bars_from_end

        if valid_mask.any():
            return indices[valid_mask], prominences[valid_mask] if len(prominences) > 0 else prominences
        else:
            # If no valid turning points, return empty
            return np.array([]), np.array([])

    # Filter peaks and troughs
    if len(peaks_idx) > 0 and 'prominences' in peak_props:
        filtered_peaks_idx, filtered_peaks_prom = filter_recent_turning_points(
            peaks_idx, peak_props['prominences']
        )
    else:
        filtered_peaks_idx, filtered_peaks_prom = peaks_idx, np.array([])

    if len(troughs_idx) > 0 and 'prominences' in trough_props:
        filtered_troughs_idx, filtered_troughs_prom = filter_recent_turning_points(
            troughs_idx, trough_props['prominences']
        )
    else:
        filtered_troughs_idx, filtered_troughs_prom = troughs_idx, np.array([])

    if align_to == 'trough':
        # Prefer troughs - use MOST RECENT confirmed trough (recency matters for trading)
        if len(filtered_troughs_idx) > 0:
            # Select most recent confirmed trough (last in array)
            t_turn = filtered_troughs_idx[-1]
            turn_type = 'trough'
        elif len(filtered_peaks_idx) > 0:
            # Fallback to most recent confirmed peak
            t_turn = filtered_peaks_idx[-1]
            turn_type = 'peak'
        else:
            # Last resort: use absolute minimum (but far from end)
            search_range = recent_detrended[:-min_bars_from_end] if len(recent_detrended) > min_bars_from_end else recent_detrended
            t_turn = np.argmin(search_range)
            turn_type = 'trough'

    elif align_to == 'peak':
        # Prefer peaks - use MOST RECENT confirmed peak (recency matters for trading)
        if len(filtered_peaks_idx) > 0:
            # Select most recent confirmed peak (last in array)
            t_turn = filtered_peaks_idx[-1]
            turn_type = 'peak'
        elif len(filtered_troughs_idx) > 0:
            # Fallback to most recent confirmed trough
            t_turn = filtered_troughs_idx[-1]
            turn_type = 'trough'
        else:
            # Last resort: use absolute maximum (but far from end)
            search_range = recent_detrended[:-min_bars_from_end] if len(recent_detrended) > min_bars_from_end else recent_detrended
            t_turn = np.argmax(search_range)
            turn_type = 'peak'

    else:  # 'auto' - use most recent CONFIRMED turning point (recency matters for trading)
        # Find the most recent confirmed turning point (peak or trough)
        latest_peak_idx = filtered_peaks_idx[-1] if len(filtered_peaks_idx) > 0 else -1
        latest_trough_idx = filtered_troughs_idx[-1] if len(filtered_troughs_idx) > 0 else -1

        if latest_peak_idx > latest_trough_idx:
            # Most recent is a peak
            t_turn = latest_peak_idx
            turn_type = 'peak'
        elif latest_trough_idx >= 0:
            # Most recent is a trough
            t_turn = latest_trough_idx
            turn_type = 'trough'
        else:
            # Fallback to absolute extrema (far from end)
            search_range = recent_detrended[:-min_bars_from_end] if len(recent_detrended) > min_bars_from_end else recent_detrended
            if abs(np.max(search_range)) > abs(np.min(search_range)):
                t_turn = np.argmax(search_range)
                turn_type = 'peak'
            else:
                t_turn = np.argmin(search_range)
                turn_type = 'trough'

    # Step 5: Generate PURE sine wave using ONLY the input wavelength
    # NO adjustments based on price data - wavelength is what user specified
    total_length = len(prices) + extend_future
    t = np.arange(total_length)
    omega = 2 * np.pi / wavelength  # Use input wavelength EXACTLY

    # Calculate phase offset based on detected turning point
    # t_turn is relative to recent_detrended, convert to absolute index
    t_turn_absolute = len(detrended) - search_window + t_turn

    if turn_type == 'trough':
        # For a trough (-1), sin(θ) = -1 when θ = -π/2
        # So: omega * t_turn_absolute + phase_offset = -π/2
        # Therefore: phase_offset = -π/2 - omega * t_turn_absolute
        phase_offset = -np.pi/2 - omega * t_turn_absolute
    elif turn_type == 'peak':
        # For a peak (+1), sin(θ) = 1 when θ = π/2
        # So: omega * t_turn_absolute + phase_offset = π/2
        # Therefore: phase_offset = π/2 - omega * t_turn_absolute
        phase_offset = np.pi/2 - omega * t_turn_absolute
    else:
        # Fallback (should never happen)
        phase_offset = 0.0

    # Fixed amplitude of 1.0 (will be normalized to ±1 range)
    amplitude = 1.0

    # Generate sine wave
    sine_wave = amplitude * np.sin(omega * t + phase_offset)

    # Normalize to ±1 range
    if amplitude > 1e-10:
        sine_wave_normalized = sine_wave / amplitude
    else:
        sine_wave_normalized = sine_wave

    # Calculate current phase
    phase_at_end = omega * (len(prices) - 1) + phase_offset
    phase_degrees = (phase_at_end * 180 / np.pi) % 360

    # Step 8: Calculate EXACT peak and trough indices anchored to END of data
    # This ensures ALL symbols have peaks/troughs at same offset from "today"
    #
    # For sin(ωt): peaks at ωt = π/2 + 2πn, troughs at ωt = 3π/2 + 2πn

    peak_indices = []
    trough_indices = []

    # Find phase at the end of data (MUST include phase_offset!)
    t_end = len(prices) - 1
    phase_at_end = (omega * t_end + phase_offset) % (2 * np.pi)

    # Find the most recent peak BEFORE or AT the end
    # Peak occurs when phase = π/2
    # How many cycles back from end to the last peak?
    phase_to_peak = (np.pi/2 - phase_at_end) % (2 * np.pi)
    if phase_to_peak > np.pi:  # Wrap around
        phase_to_peak = phase_to_peak - 2*np.pi
    t_last_peak = t_end + (phase_to_peak / omega)

    # Work backwards from last peak to find all peaks (including future)
    t_peak = t_last_peak
    while t_peak >= 0:
        peak_indices.insert(0, int(round(t_peak)))
        t_peak -= wavelength

    # Work forwards from last peak to find future peaks
    t_peak = t_last_peak + wavelength
    while t_peak < total_length:
        peak_indices.append(int(round(t_peak)))
        t_peak += wavelength

    # Find the most recent trough BEFORE or AT the end
    # Trough occurs when phase = 3π/2
    phase_to_trough = (3*np.pi/2 - phase_at_end) % (2 * np.pi)
    if phase_to_trough > np.pi:
        phase_to_trough = phase_to_trough - 2*np.pi
    t_last_trough = t_end + (phase_to_trough / omega)

    # Work backwards from last trough to find all troughs (including future)
    t_trough = t_last_trough
    while t_trough >= 0:
        trough_indices.insert(0, int(round(t_trough)))
        t_trough -= wavelength

    # Work forwards from last trough to find future troughs
    t_trough = t_last_trough + wavelength
    while t_trough < total_length:
        trough_indices.append(int(round(t_trough)))
        t_trough += wavelength

    # Step 6: Filter out labels too close to the data end (developing/unconfirmed)
    # For trading purposes, exclude turning points within last 25% of wavelength
    # This prevents showing labels for price action that's still developing
    # Also exclude future projections - only show confirmed historical turning points
    data_end = len(prices) - 1  # Last actual data point (not including future projection)
    min_bars_from_end = int(wavelength * 0.25)

    # Filter peaks: keep only confirmed peaks within actual data range
    # Exclude: (1) developing peaks within last 25% of wavelength, (2) future projections
    confirmed_peaks = [idx for idx in peak_indices if 0 <= idx <= data_end - min_bars_from_end]

    # Filter troughs: keep only confirmed troughs within actual data range
    # Exclude: (1) developing troughs within last 25% of wavelength, (2) future projections
    confirmed_troughs = [idx for idx in trough_indices if 0 <= idx <= data_end - min_bars_from_end]

    return {
        'bandpass_normalized': sine_wave_normalized,
        'method': f'V10_pure_sine',
        'phase_degrees': float(phase_degrees),
        'amplitude': float(amplitude),
        'wavelength': float(wavelength),
        'peaks': confirmed_peaks,
        'troughs': confirmed_troughs,
        'effective_wavelength': float(wavelength)
    }


def _create_bandpass_hilbert_phase(prices, wavelength, bandwidth_pct, extend_future, align_to='trough'):
    """
    ALTERNATIVE METHOD - uses Hilbert transform for instantaneous phase

    This method:
    1. Detrends prices
    2. Applies Butterworth bandpass filter (clean, no FFT phase issues)
    3. Uses Hilbert transform to extract instantaneous phase
    4. Finds actual price peaks and validates with Hilbert phase

    Args:
        align_to: 'trough' (default), 'peak', or 'auto' (phase-validated)
    """

    # Step 1: Detrend
    x = np.arange(len(prices))
    try:
        coeffs = np.polyfit(x, prices, 3)
        trend = np.polyval(coeffs, x)
        detrended = prices - trend
    except:
        detrended = prices - np.mean(prices)

    # Step 2: Apply Butterworth bandpass filter (better than FFT for phase)
    # Nyquist frequency (sampling rate = 1 sample per day)
    nyquist = 0.5

    # Filter frequencies
    low_period = wavelength * (1 + bandwidth_pct)
    high_period = wavelength * (1 - bandwidth_pct)

    low_freq = 1.0 / low_period / nyquist
    high_freq = 1.0 / high_period / nyquist

    # Ensure frequencies are in valid range (0, 1)
    low_freq = max(0.001, min(0.999, low_freq))
    high_freq = max(0.001, min(0.999, high_freq))

    if low_freq >= high_freq:
        # Bandwidth too narrow, use wider filter
        low_freq = 1.0 / (wavelength * 1.2) / nyquist
        high_freq = 1.0 / (wavelength * 0.8) / nyquist

    try:
        # Use 4th order Butterworth for sharp cutoff
        b, a = butter(4, [low_freq, high_freq], btype='band')
        filtered = filtfilt(b, a, detrended)
    except:
        # Fallback to FFT method if Butterworth fails
        return _create_bandpass_v9_method(prices, wavelength, bandwidth_pct, extend_future)

    # Step 3: Apply Hilbert transform to get instantaneous phase
    analytic_signal = hilbert(filtered)
    instantaneous_phase = np.angle(analytic_signal)
    instantaneous_amplitude = np.abs(analytic_signal)

    # Step 4: Find actual price peaks and validate with Hilbert phase
    search_window = min(len(detrended), int(wavelength * 2.5))
    recent_detrended = detrended[-search_window:]
    recent_phase = instantaneous_phase[-search_window:]

    min_peak_distance = int(wavelength * 0.4)

    peaks_idx, _ = find_peaks(recent_detrended, distance=min_peak_distance)
    troughs_idx, _ = find_peaks(-recent_detrended, distance=min_peak_distance)

    # Find turning point with phase validation based on align_to preference
    best_turn_idx = None
    best_turn_type = None

    if align_to == 'trough':
        # Prefer troughs (phase should be near -π/2)
        for idx in reversed(troughs_idx):
            phase_at_trough = recent_phase[idx]
            phase_error = min(
                abs(phase_at_trough - (-np.pi/2)),
                abs(phase_at_trough - (3*np.pi/2))
            )
            if phase_error < np.pi/3:
                best_turn_idx = idx
                best_turn_type = 'trough'
                break
        # Fallback to most recent trough
        if best_turn_idx is None and len(troughs_idx) > 0:
            best_turn_idx = troughs_idx[-1]
            best_turn_type = 'trough'
        elif best_turn_idx is None and len(peaks_idx) > 0:
            best_turn_idx = peaks_idx[-1]
            best_turn_type = 'peak'
        elif best_turn_idx is None:
            best_turn_idx = np.argmin(recent_detrended)
            best_turn_type = 'trough'

    elif align_to == 'peak':
        # Prefer peaks (phase should be near π/2)
        for idx in reversed(peaks_idx):
            phase_at_peak = recent_phase[idx]
            phase_error = abs(phase_at_peak - (np.pi/2))
            if phase_error < np.pi/3:
                best_turn_idx = idx
                best_turn_type = 'peak'
                break
        # Fallback to most recent peak
        if best_turn_idx is None and len(peaks_idx) > 0:
            best_turn_idx = peaks_idx[-1]
            best_turn_type = 'peak'
        elif best_turn_idx is None and len(troughs_idx) > 0:
            best_turn_idx = troughs_idx[-1]
            best_turn_type = 'trough'
        elif best_turn_idx is None:
            best_turn_idx = np.argmax(recent_detrended)
            best_turn_type = 'peak'

    else:  # 'auto' - phase-validated (original logic)
        # Check troughs first
        for idx in reversed(troughs_idx):
            phase_at_trough = recent_phase[idx]
            phase_error = min(
                abs(phase_at_trough - (-np.pi/2)),
                abs(phase_at_trough - (3*np.pi/2))
            )
            if phase_error < np.pi/3:
                best_turn_idx = idx
                best_turn_type = 'trough'
                break
        # Then check peaks if no valid trough
        if best_turn_idx is None:
            for idx in reversed(peaks_idx):
                phase_at_peak = recent_phase[idx]
                phase_error = abs(phase_at_peak - (np.pi/2))
                if phase_error < np.pi/3:
                    best_turn_idx = idx
                    best_turn_type = 'peak'
                    break
        # Fallback to most recent
        if best_turn_idx is None:
            if len(troughs_idx) > 0 and len(peaks_idx) > 0:
                if troughs_idx[-1] > peaks_idx[-1]:
                    best_turn_idx = troughs_idx[-1]
                    best_turn_type = 'trough'
                else:
                    best_turn_idx = peaks_idx[-1]
                    best_turn_type = 'peak'
            elif len(troughs_idx) > 0:
                best_turn_idx = troughs_idx[-1]
                best_turn_type = 'trough'
            elif len(peaks_idx) > 0:
                best_turn_idx = peaks_idx[-1]
                best_turn_type = 'peak'
            else:
                best_turn_idx = np.argmin(np.abs(recent_detrended))
                best_turn_type = 'trough' if recent_detrended[best_turn_idx] < 0 else 'peak'

    # Convert to absolute index
    t_turn_absolute = len(detrended) - search_window + best_turn_idx

    # Step 5: Calculate amplitude from Hilbert envelope
    amplitude = np.median(instantaneous_amplitude[-search_window:])
    if amplitude < 1e-10:
        amplitude = np.std(filtered)
    if amplitude < 1e-10:
        amplitude = 1.0

    # Step 6: Generate sine wave
    total_length = len(prices) + extend_future
    t = np.arange(total_length)
    omega = 2 * np.pi / wavelength

    if best_turn_type == 'peak':
        phase_offset = np.pi / 2 - omega * t_turn_absolute
    else:
        phase_offset = -np.pi / 2 - omega * t_turn_absolute

    sine_wave = amplitude * np.sin(omega * t + phase_offset)

    if amplitude > 1e-10:
        sine_wave_normalized = sine_wave / amplitude
    else:
        sine_wave_normalized = sine_wave

    phase_at_end = omega * (len(prices) - 1) + phase_offset
    phase_degrees = (phase_at_end * 180 / np.pi) % 360

    return {
        'bandpass_normalized': sine_wave_normalized,
        'method': f'V10_hilbert_phase_{best_turn_type}s',
        'phase_degrees': float(phase_degrees),
        'amplitude': float(amplitude),
        'wavelength': wavelength,
        't_turn_index': int(t_turn_absolute),
        'turn_type': best_turn_type
    }
