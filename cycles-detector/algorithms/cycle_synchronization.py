#!/usr/bin/env python3
"""
CYCLE SYNCHRONIZATION ANALYZER
===============================
Detects when multiple cycles align at troughs for high-confidence trading signals.

Based on Hurst's principle:
- Only buy when trade cycle AND two longer cycles are rising
- Multiple cycle troughs aligning = high confidence entry point
"""

import numpy as np
from scipy.signal import find_peaks


class CycleSynchronizationAnalyzer:
    def __init__(self, alignment_tolerance=10):
        """
        Args:
            alignment_tolerance: Days within which troughs are considered "aligned" (default: 10)
        """
        self.alignment_tolerance = alignment_tolerance

    def find_cycle_troughs_and_peaks(self, bandpass_signal, wavelength):
        """
        Find all troughs (buy signals) and peaks (sell signals) for a cycle.

        Args:
            bandpass_signal: The bandpass filtered cycle signal
            wavelength: Cycle wavelength in days

        Returns:
            dict with 'troughs' and 'peaks' indices, and current phase info
        """
        # Find troughs (minima) - buy signals
        troughs, _ = find_peaks(-bandpass_signal, distance=wavelength//4)

        # Find peaks (maxima) - sell signals
        peaks, _ = find_peaks(bandpass_signal, distance=wavelength//4)

        # Determine current phase (is cycle rising or falling?)
        current_idx = len(bandpass_signal) - 1
        current_value = bandpass_signal[current_idx]

        # Find nearest trough and peak
        nearest_trough_idx = None
        nearest_peak_idx = None

        if len(troughs) > 0:
            # Find most recent trough
            past_troughs = troughs[troughs <= current_idx]
            if len(past_troughs) > 0:
                nearest_trough_idx = past_troughs[-1]

        if len(peaks) > 0:
            # Find most recent peak
            past_peaks = peaks[peaks <= current_idx]
            if len(past_peaks) > 0:
                nearest_peak_idx = past_peaks[-1]

        # Determine if rising (trough more recent than peak)
        is_rising = False
        if nearest_trough_idx is not None and nearest_peak_idx is not None:
            is_rising = nearest_trough_idx > nearest_peak_idx
        elif nearest_trough_idx is not None:
            is_rising = True  # Only trough found, assume rising

        # Days since last trough
        days_since_trough = None
        if nearest_trough_idx is not None:
            days_since_trough = current_idx - nearest_trough_idx

        return {
            'troughs': troughs,
            'peaks': peaks,
            'is_rising': is_rising,
            'nearest_trough_idx': nearest_trough_idx,
            'nearest_peak_idx': nearest_peak_idx,
            'days_since_trough': days_since_trough,
            'current_value': current_value
        }

    def detect_trough_alignments(self, cycles_data):
        """
        Detect when multiple cycle troughs align within tolerance.

        Args:
            cycles_data: List of cycle dicts with 'wavelength', 'bandpass', 'phase_info'

        Returns:
            List of alignment events with confidence scores
        """
        # Get trough/peak info for all cycles
        cycle_phases = []
        for cycle in cycles_data:
            phase_info = self.find_cycle_troughs_and_peaks(
                cycle['bandpass'],
                cycle['wavelength']
            )
            cycle_phases.append({
                'wavelength': cycle['wavelength'],
                'phase_info': phase_info,
                'cycle': cycle
            })

        # Find current alignment (most recent troughs)
        recent_troughs = []
        for cp in cycle_phases:
            if cp['phase_info']['nearest_trough_idx'] is not None:
                recent_troughs.append({
                    'wavelength': cp['wavelength'],
                    'trough_idx': cp['phase_info']['nearest_trough_idx'],
                    'days_since': cp['phase_info']['days_since_trough'],
                    'is_rising': cp['phase_info']['is_rising']
                })

        if len(recent_troughs) == 0:
            return []

        # Find alignments (troughs within tolerance of each other)
        alignments = []

        # Group troughs by proximity
        sorted_troughs = sorted(recent_troughs, key=lambda x: x['trough_idx'])

        current_group = [sorted_troughs[0]]

        for i in range(1, len(sorted_troughs)):
            trough = sorted_troughs[i]
            reference_idx = current_group[0]['trough_idx']

            if abs(trough['trough_idx'] - reference_idx) <= self.alignment_tolerance:
                # Within tolerance, add to current group
                current_group.append(trough)
            else:
                # Start new group
                if len(current_group) >= 2:
                    # Save previous group if significant
                    alignments.append(self._create_alignment_event(current_group))
                current_group = [trough]

        # Don't forget last group
        if len(current_group) >= 2:
            alignments.append(self._create_alignment_event(current_group))

        return alignments

    def _create_alignment_event(self, trough_group):
        """Create alignment event from group of troughs."""
        avg_idx = int(np.mean([t['trough_idx'] for t in trough_group]))
        wavelengths = [t['wavelength'] for t in trough_group]
        num_cycles = len(trough_group)

        # Confidence score based on number of aligned cycles
        if num_cycles >= 5:
            confidence = "Very High"
            color = "#00ff00"  # Bright green
        elif num_cycles >= 3:
            confidence = "High"
            color = "#88ff88"  # Light green
        elif num_cycles >= 2:
            confidence = "Moderate"
            color = "#ffff44"  # Yellow
        else:
            confidence = "Low"
            color = "#888888"  # Gray

        return {
            'alignment_idx': int(avg_idx),
            'num_cycles': int(num_cycles),
            'wavelengths': [int(w) for w in sorted(wavelengths)],
            'confidence': confidence,
            'color': color,
            'days_ago': int(trough_group[0]['days_since']) if trough_group[0]['days_since'] is not None else None
        }

    def check_hurst_buy_signal(self, cycles_data, trade_cycle_wavelength=None):
        """
        Check Hurst's rule: Only buy when trade cycle AND two longer cycles are rising.

        Args:
            cycles_data: List of cycle dicts with wavelength and bandpass
            trade_cycle_wavelength: Wavelength to use as "trade cycle" (default: shortest cycle)

        Returns:
            dict with buy_signal (bool), details, and confidence
        """
        # Get phase info for all cycles
        cycle_phases = []
        for cycle in cycles_data:
            phase_info = self.find_cycle_troughs_and_peaks(
                cycle['bandpass'],
                cycle['wavelength']
            )
            cycle_phases.append({
                'wavelength': cycle['wavelength'],
                'phase_info': phase_info,
                'cycle': cycle
            })

        # Sort by wavelength
        cycle_phases.sort(key=lambda x: x['wavelength'])

        if len(cycle_phases) < 3:
            return {
                'buy_signal': False,
                'reason': 'Need at least 3 cycles for Hurst rule',
                'confidence': 'N/A',
                'rising_cycles': []
            }

        # Identify trade cycle (default: shortest)
        if trade_cycle_wavelength is None:
            trade_cycle = cycle_phases[0]
        else:
            trade_cycle = next((c for c in cycle_phases if c['wavelength'] == trade_cycle_wavelength), cycle_phases[0])

        # Find longer cycles
        longer_cycles = [c for c in cycle_phases if c['wavelength'] > trade_cycle['wavelength']]

        if len(longer_cycles) < 2:
            return {
                'buy_signal': False,
                'reason': 'Need at least 2 cycles longer than trade cycle',
                'confidence': 'N/A',
                'rising_cycles': []
            }

        # Check if trade cycle is rising
        trade_rising = trade_cycle['phase_info']['is_rising']

        # Check how many longer cycles are rising
        rising_longer = [c for c in longer_cycles if c['phase_info']['is_rising']]

        # Hurst rule: trade cycle + at least 2 longer cycles rising
        buy_signal = trade_rising and len(rising_longer) >= 2

        # Confidence based on how many cycles are rising
        total_rising = len(rising_longer) + (1 if trade_rising else 0)

        if total_rising >= 5:
            confidence = "Very High"
        elif total_rising >= 4:
            confidence = "High"
        elif total_rising >= 3:
            confidence = "Moderate"
        else:
            confidence = "Low"

        return {
            'buy_signal': buy_signal,
            'trade_cycle_wavelength': trade_cycle['wavelength'],
            'trade_cycle_rising': trade_rising,
            'longer_cycles_rising': len(rising_longer),
            'total_cycles_rising': total_rising,
            'confidence': confidence,
            'rising_cycles': [c['wavelength'] for c in rising_longer],
            'reason': f"Trade cycle ({trade_cycle['wavelength']}d) {'rising' if trade_rising else 'falling'}, {len(rising_longer)} longer cycles rising"
        }

    def get_current_sync_status(self, cycles_data):
        """
        Get overall synchronization status at current bar.

        Args:
            cycles_data: List of cycle dicts

        Returns:
            dict with sync status, visual zone color, and details
        """
        # Check alignments
        alignments = self.detect_trough_alignments(cycles_data)

        # Check Hurst buy signal
        hurst_signal = self.check_hurst_buy_signal(cycles_data)

        # Count rising cycles
        rising_count = 0
        total_count = len(cycles_data)

        for cycle in cycles_data:
            phase_info = self.find_cycle_troughs_and_peaks(cycle['bandpass'], cycle['wavelength'])
            if phase_info['is_rising']:
                rising_count += 1

        # Determine overall sync status
        rising_pct = (rising_count / total_count * 100) if total_count > 0 else 0

        # Visual zone color
        if hurst_signal['buy_signal'] and hurst_signal['confidence'] in ['High', 'Very High']:
            zone_color = "#00ff0033"  # Green with transparency
            sync_status = "Strong Synchronization"
            confidence = "High"
        elif rising_pct >= 60:
            zone_color = "#ffff0033"  # Yellow with transparency
            sync_status = "Partial Synchronization"
            confidence = "Moderate"
        elif rising_pct >= 40:
            zone_color = "#ff880033"  # Orange with transparency
            sync_status = "Weak Synchronization"
            confidence = "Low"
        else:
            zone_color = "#ff000033"  # Red with transparency
            sync_status = "No Synchronization"
            confidence = "Very Low"

        return {
            'sync_status': sync_status,
            'confidence': confidence,
            'zone_color': zone_color,
            'rising_cycles': rising_count,
            'total_cycles': total_count,
            'rising_percentage': round(rising_pct, 1),
            'alignments': alignments,
            'hurst_signal': hurst_signal
        }


# Standalone testing
if __name__ == "__main__":
    print("Testing Cycle Synchronization Analyzer...")

    # Mock data
    import numpy as np

    # Create mock bandpass signals
    n_bars = 1000

    cycles = [
        {
            'wavelength': 90,
            'bandpass': np.sin(2 * np.pi * np.arange(n_bars) / 90) + np.random.randn(n_bars) * 0.1
        },
        {
            'wavelength': 180,
            'bandpass': np.sin(2 * np.pi * np.arange(n_bars) / 180) + np.random.randn(n_bars) * 0.1
        },
        {
            'wavelength': 360,
            'bandpass': np.sin(2 * np.pi * np.arange(n_bars) / 360) + np.random.randn(n_bars) * 0.1
        },
    ]

    analyzer = CycleSynchronizationAnalyzer(alignment_tolerance=10)

    # Test synchronization detection
    sync_status = analyzer.get_current_sync_status(cycles)

    print(f"\n=== Current Synchronization Status ===")
    print(f"Status: {sync_status['sync_status']}")
    print(f"Confidence: {sync_status['confidence']}")
    print(f"Rising Cycles: {sync_status['rising_cycles']}/{sync_status['total_cycles']} ({sync_status['rising_percentage']}%)")
    print(f"Zone Color: {sync_status['zone_color']}")

    print(f"\n=== Hurst Buy Signal ===")
    hurst = sync_status['hurst_signal']
    print(f"Buy Signal: {hurst['buy_signal']}")
    print(f"Reason: {hurst['reason']}")
    print(f"Confidence: {hurst['confidence']}")

    print(f"\n=== Trough Alignments ===")
    for i, alignment in enumerate(sync_status['alignments']):
        print(f"\nAlignment {i+1}:")
        print(f"  Cycles aligned: {alignment['num_cycles']}")
        print(f"  Wavelengths: {alignment['wavelengths']}")
        print(f"  Confidence: {alignment['confidence']}")
        print(f"  Days ago: {alignment['days_ago']}")
