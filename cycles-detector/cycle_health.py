#!/usr/bin/env python3
"""
CYCLE HEALTH METRICS
Tracks amplitude consistency and wavelength stability over time
"""

import numpy as np
from scipy.signal import find_peaks as scipy_find_peaks


def calculate_cycle_health(bandpass, expected_wavelength_trading_days, lookback_cycles=3):
    """
    Calculate cycle health metrics

    Args:
        bandpass: Normalized bandpass signal array
        expected_wavelength_trading_days: Expected cycle period in trading days
        lookback_cycles: Number of recent cycles to compare (default 3)

    Returns:
        dict with health metrics and score
    """

    # Find peaks and troughs
    peaks, _ = scipy_find_peaks(bandpass, distance=int(expected_wavelength_trading_days * 0.4))
    troughs, _ = scipy_find_peaks(-bandpass, distance=int(expected_wavelength_trading_days * 0.4))

    if len(peaks) < 4 or len(troughs) < 4:
        return {
            'score': 50,
            'status': '🟡 Insufficient data',
            'amplitude_health': 'Not enough cycles',
            'wavelength_health': 'Not enough cycles',
            'amplitude_trend': 0,
            'wavelength_drift': 0
        }

    # 1. AMPLITUDE CONSISTENCY CHECK
    amplitudes = []
    for i in range(len(peaks) - 1):
        # Find trough between consecutive peaks
        troughs_between = [t for t in troughs if peaks[i] < t < peaks[i+1]]
        if troughs_between:
            trough_idx = troughs_between[0]
            amp = bandpass[peaks[i]] - bandpass[trough_idx]
            amplitudes.append(abs(amp))

    if len(amplitudes) < 4:
        return {
            'score': 50,
            'status': '🟡 Insufficient data',
            'amplitude_health': 'Not enough cycles',
            'wavelength_health': 'Not enough cycles',
            'amplitude_trend': 0,
            'wavelength_drift': 0
        }

    # Split into recent vs historical
    lookback = min(lookback_cycles, len(amplitudes) // 2)
    recent_amps = amplitudes[-lookback:]
    historical_amps = amplitudes[:-lookback]

    recent_amp_avg = np.mean(recent_amps)
    historical_amp_avg = np.mean(historical_amps)

    # Calculate amplitude change percentage
    if historical_amp_avg > 0:
        amp_change_pct = ((recent_amp_avg - historical_amp_avg) / historical_amp_avg) * 100
    else:
        amp_change_pct = 0

    # 2. WAVELENGTH STABILITY CHECK
    measured_wavelengths = []
    for i in range(len(peaks) - 1):
        period = peaks[i+1] - peaks[i]
        measured_wavelengths.append(period)

    recent_wls = measured_wavelengths[-lookback:]
    historical_wls = measured_wavelengths[:-lookback]

    recent_wl_avg = np.mean(recent_wls)
    historical_wl_avg = np.mean(historical_wls)

    # Calculate wavelength drift percentage
    wavelength_drift_pct = ((recent_wl_avg - expected_wavelength_trading_days) / expected_wavelength_trading_days) * 100

    # Calculate wavelength variance (consistency)
    wl_variance_pct = (np.std(recent_wls) / np.mean(recent_wls)) * 100 if len(recent_wls) > 0 else 0

    # 3. CALCULATE HEALTH SCORE (0-100)
    health_score = 100

    # Deduct for amplitude degradation
    if amp_change_pct < -50:
        health_score -= 40
        amp_status = f"🔴 Weakening ({amp_change_pct:.1f}%)"
    elif amp_change_pct < -25:
        health_score -= 25
        amp_status = f"⚠️ Declining ({amp_change_pct:.1f}%)"
    elif amp_change_pct < -10:
        health_score -= 10
        amp_status = f"🟡 Slightly down ({amp_change_pct:.1f}%)"
    else:
        amp_status = f"✅ Stable ({amp_change_pct:+.1f}%)"

    # Deduct for wavelength drift
    abs_drift = abs(wavelength_drift_pct)
    if abs_drift > 20:
        health_score -= 35
        wl_status = f"🔴 Drifting ({wavelength_drift_pct:+.1f}%)"
    elif abs_drift > 10:
        health_score -= 20
        wl_status = f"⚠️ Shifting ({wavelength_drift_pct:+.1f}%)"
    elif abs_drift > 5:
        health_score -= 10
        wl_status = f"🟡 Minor drift ({wavelength_drift_pct:+.1f}%)"
    else:
        wl_status = f"✅ Stable ({wavelength_drift_pct:+.1f}%)"

    # Deduct for high variance
    if wl_variance_pct > 25:
        health_score -= 15
        wl_status += " (erratic)"
    elif wl_variance_pct > 15:
        health_score -= 8

    # 4. DETERMINE OVERALL STATUS
    if health_score >= 80:
        overall_status = "🟢 Healthy"
        badge = "🟢"
    elif health_score >= 60:
        overall_status = "🟡 Degrading"
        badge = "🟡"
    else:
        overall_status = "🔴 Unstable"
        badge = "🔴"

    return {
        'score': int(health_score),
        'status': overall_status,
        'badge': badge,
        'amplitude_health': amp_status,
        'wavelength_health': wl_status,
        'amplitude_trend': round(amp_change_pct, 1),
        'wavelength_drift': round(wavelength_drift_pct, 1),
        'details': {
            'recent_amplitude': round(recent_amp_avg, 3),
            'historical_amplitude': round(historical_amp_avg, 3),
            'recent_wavelength': round(recent_wl_avg, 1),
            'expected_wavelength': round(expected_wavelength_trading_days, 1),
            'wavelength_variance': round(wl_variance_pct, 1)
        }
    }
