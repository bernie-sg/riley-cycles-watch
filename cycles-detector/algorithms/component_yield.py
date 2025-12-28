#!/usr/bin/env python3
"""
COMPONENT YIELD CALCULATION
============================
Brute force time frequency analysis with amplitude replaced by yield.
Measures the theoretical trading performance of a specific cycle frequency.
"""

import numpy as np
from scipy.signal import find_peaks


def calculate_component_yield(bandpass_signal, prices, wavelength):
    """
    Calculate the component yield over sample for a bandpass signal.

    This simulates perfect trading at peaks (sell) and troughs (buy) of the
    bandpass signal, returning the cumulative yield percentage.

    Args:
        bandpass_signal: The bandpass filtered signal (oscillating around 0)
        prices: Original price data (same length as bandpass_signal)
        wavelength: The wavelength in trading days

    Returns:
        dict with:
            - yield_percent: Total yield percentage over the sample
            - num_trades: Number of complete buy-sell cycles
            - trades: List of trade dictionaries
    """

    if len(bandpass_signal) < wavelength:
        return {
            'yield_percent': 0.0,
            'num_trades': 0,
            'trades': []
        }

    # Find peaks (sell signals) and troughs (buy signals)
    peaks, _ = find_peaks(bandpass_signal, distance=wavelength//4)
    troughs, _ = find_peaks(-bandpass_signal, distance=wavelength//4)

    if len(peaks) == 0 or len(troughs) == 0:
        return {
            'yield_percent': 0.0,
            'num_trades': 0,
            'trades': []
        }

    # Create buy/sell sequence
    # Strategy: Buy at troughs, sell at peaks
    events = []
    for trough_idx in troughs:
        events.append(('buy', trough_idx, prices[trough_idx]))
    for peak_idx in peaks:
        events.append(('sell', peak_idx, prices[peak_idx]))

    # Sort by time
    events.sort(key=lambda x: x[1])

    # Execute trades
    position = None  # None or ('long', entry_price, entry_idx)
    cumulative_yield = 0.0
    trades = []

    for action, idx, price in events:
        if action == 'buy' and position is None:
            # Enter long position
            position = ('long', price, idx)

        elif action == 'sell' and position is not None:
            # Exit long position
            entry_price = position[1]
            entry_idx = position[2]

            # Calculate yield for this trade
            trade_return = ((price - entry_price) / entry_price) * 100
            cumulative_yield += trade_return

            trades.append({
                'entry_idx': entry_idx,
                'exit_idx': idx,
                'entry_price': entry_price,
                'exit_price': price,
                'return_pct': trade_return
            })

            position = None

    return {
        'yield_percent': round(cumulative_yield, 2),
        'num_trades': len(trades),
        'trades': trades
    }


def get_yield_rating(yield_percent):
    """
    Rate the component yield based on Sigma-L criteria.

    Args:
        yield_percent: Component yield percentage

    Returns:
        dict with rating class and description
    """

    if yield_percent >= 100:
        rating_class = 'A/B'
        description = 'Excellent - Strong tradeable cycle'
        color = '#00ff00'  # Green
    elif yield_percent >= 50:
        rating_class = 'C'
        description = 'Good - Moderate performance'
        color = '#ffaa00'  # Orange
    else:
        rating_class = 'D'
        description = 'Weak - Low performance'
        color = '#ff4444'  # Red

    return {
        'class': rating_class,
        'description': description,
        'color': color
    }


def calculate_running_yield(bandpass_signal, prices, wavelength, window_step=20):
    """
    Calculate running cumulative yield over time (for heatmap visualization).

    Args:
        bandpass_signal: The bandpass filtered signal
        prices: Original price data
        wavelength: The wavelength in trading days
        window_step: Step size for sliding window (default: 20 days)

    Returns:
        List of (time_idx, cumulative_yield) tuples
    """

    running_yields = []

    # Start from first full cycle
    start_idx = wavelength

    for end_idx in range(start_idx, len(bandpass_signal), window_step):
        # Calculate yield for window [0:end_idx]
        window_signal = bandpass_signal[:end_idx]
        window_prices = prices[:end_idx]

        result = calculate_component_yield(window_signal, window_prices, wavelength)
        running_yields.append((end_idx, result['yield_percent']))

    return running_yields
