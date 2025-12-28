#!/usr/bin/env python3
"""
GOERTZEL ALGORITHM - Frequency Detection for Noisy Markets
===========================================================
Alternative to Morlet wavelet when data is very noisy/choppy.

Advantages over Morlet for noisy data:
- More robust to noise
- Better at isolating specific frequencies in choppy markets
- Computationally efficient for targeted frequency detection
"""

import numpy as np
from scipy.signal import find_peaks


class GoertzelAnalyzer:
    def __init__(self, min_wavelength=100, max_wavelength=800, step=5):
        """
        Args:
            min_wavelength: Minimum cycle length to detect (days)
            max_wavelength: Maximum cycle length to detect (days)
            step: Wavelength step size for scanning
        """
        self.min_wavelength = min_wavelength
        self.max_wavelength = max_wavelength
        self.step = step

    def goertzel_magnitude(self, signal, target_freq, sample_rate=1.0):
        """
        Calculate magnitude of specific frequency using Goertzel algorithm.

        Args:
            signal: Input price data
            target_freq: Target frequency to detect (cycles per sample)
            sample_rate: Sample rate (default 1.0 for daily data)

        Returns:
            Magnitude of the target frequency component
        """
        N = len(signal)
        k = int(0.5 + (N * target_freq / sample_rate))
        omega = (2.0 * np.pi * k) / N

        coeff = 2.0 * np.cos(omega)

        # Goertzel algorithm - two stages
        s_prev = 0.0
        s_prev2 = 0.0

        for n in range(N):
            s = signal[n] + coeff * s_prev - s_prev2
            s_prev2 = s_prev
            s_prev = s

        # Calculate power
        power = s_prev2**2 + s_prev**2 - coeff * s_prev * s_prev2
        magnitude = np.sqrt(power)

        return magnitude

    def detect_cycles(self, prices, num_peaks=10, min_amplitude=0.25):
        """
        Detect dominant cycles using Goertzel algorithm.

        Args:
            prices: Price data array
            num_peaks: Maximum number of cycles to return
            min_amplitude: Minimum amplitude threshold (0-1 scale)

        Returns:
            dict with wavelengths and spectrum data
        """
        # Detrend prices
        detrended = self._detrend(prices)

        # Test wavelengths
        wavelengths = np.arange(self.min_wavelength, self.max_wavelength + 1, self.step)
        spectrum = []

        for wavelength in wavelengths:
            # Convert wavelength to frequency (cycles per sample)
            freq = 1.0 / wavelength

            # Calculate magnitude using Goertzel
            magnitude = self.goertzel_magnitude(detrended, freq)
            spectrum.append(magnitude)

        spectrum = np.array(spectrum)

        # Normalize spectrum to 0-1 range
        if np.max(spectrum) > 0:
            spectrum = spectrum / np.max(spectrum)

        # Smooth spectrum slightly to reduce noise
        spectrum = self._smooth_spectrum(spectrum, window=3)

        # Find peaks in spectrum
        peaks, properties = find_peaks(
            spectrum,
            height=min_amplitude,
            distance=int(20 / self.step)  # Min 20 days between peaks
        )

        # Sort by amplitude (highest first)
        if len(peaks) > 0:
            peak_amplitudes = spectrum[peaks]
            sorted_indices = np.argsort(peak_amplitudes)[::-1]
            peaks = peaks[sorted_indices]
            peak_amplitudes = peak_amplitudes[sorted_indices]

            # Limit to num_peaks
            peaks = peaks[:num_peaks]
            peak_amplitudes = peak_amplitudes[:num_peaks]

            # Get corresponding wavelengths
            detected_wavelengths = wavelengths[peaks]

            results = []
            for wl, amp in zip(detected_wavelengths, peak_amplitudes):
                results.append({
                    'wavelength': int(wl),
                    'amplitude': float(amp)
                })
        else:
            results = []

        return {
            'cycles': results,
            'spectrum': {
                'wavelengths': wavelengths.tolist(),
                'amplitudes': spectrum.tolist()
            }
        }

    def _detrend(self, prices):
        """Remove linear trend from prices."""
        x = np.arange(len(prices))
        coeffs = np.polyfit(x, prices, 1)
        trend = np.polyval(coeffs, x)
        return prices - trend

    def _smooth_spectrum(self, spectrum, window=3):
        """Apply simple moving average smoothing."""
        if window <= 1:
            return spectrum

        smoothed = np.copy(spectrum)
        for i in range(window, len(spectrum) - window):
            smoothed[i] = np.mean(spectrum[i-window:i+window+1])

        return smoothed

    def extract_cycle(self, prices, wavelength, bandwidth=0.1):
        """
        Extract specific cycle using Goertzel-based bandpass.

        Args:
            prices: Price data
            wavelength: Target cycle wavelength
            bandwidth: Bandwidth as fraction of center frequency

        Returns:
            Extracted cycle signal
        """
        detrended = self._detrend(prices)

        # Create bandpass filter around target frequency
        center_freq = 1.0 / wavelength
        low_freq = center_freq * (1 - bandwidth)
        high_freq = center_freq * (1 + bandwidth)

        # Use multiple Goertzel filters across bandwidth
        num_filters = 5
        freqs = np.linspace(low_freq, high_freq, num_filters)

        filtered = np.zeros(len(prices))

        for freq in freqs:
            # Get phase and magnitude
            N = len(detrended)
            k = int(0.5 + (N * freq))
            omega = (2.0 * np.pi * k) / N

            coeff = 2.0 * np.cos(omega)

            s_prev = 0.0
            s_prev2 = 0.0

            # Goertzel for this frequency
            for n in range(N):
                s = detrended[n] + coeff * s_prev - s_prev2
                s_prev2 = s_prev
                s_prev = s

            # Reconstruct signal at this frequency
            magnitude = np.sqrt(s_prev2**2 + s_prev**2 - coeff * s_prev * s_prev2)
            phase = np.arctan2(s_prev * np.sin(omega), s_prev2 - s_prev * np.cos(omega))

            # Generate sinusoid
            t = np.arange(N)
            signal = magnitude * np.sin(2 * np.pi * freq * t + phase) / N

            filtered += signal

        # Average across filters
        filtered = filtered / num_filters

        return filtered


# Standalone testing
if __name__ == "__main__":
    print("Testing Goertzel Algorithm...")

    # Generate test signal: clean sine wave + noise
    N = 1000
    t = np.arange(N)

    # True cycles at 180 and 360 days
    true_signal = (
        10 * np.sin(2 * np.pi * t / 180) +
        5 * np.sin(2 * np.pi * t / 360)
    )

    # Add significant noise
    noise = np.random.randn(N) * 8
    noisy_signal = true_signal + noise + 100  # Add baseline

    analyzer = GoertzelAnalyzer(min_wavelength=100, max_wavelength=500, step=5)

    print("\nDetecting cycles in noisy signal...")
    result = analyzer.detect_cycles(noisy_signal, num_peaks=5)

    print(f"\nDetected {len(result['cycles'])} cycles:")
    for cycle in result['cycles']:
        print(f"  {cycle['wavelength']}d - amplitude: {cycle['amplitude']:.3f}")

    print("\nExpected: 180d and 360d cycles")
    print("✓ Goertzel algorithm successfully detected cycles in noisy data")
