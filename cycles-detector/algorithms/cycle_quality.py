"""
Cycle Quality Analyzer - SNR & Harmonic Validation (V12)

This module provides cycle quality scoring based on:
1. Signal-to-Noise Ratio (SNR)
2. Harmonic family membership (Hurst's principle)

Returns 1-4 star ratings instead of A/B/C/D to avoid confusion with existing rating system.
"""

import numpy as np
from scipy import signal

class CycleQualityAnalyzer:
    def __init__(self, min_snr=3.0, harmonic_tolerance=0.15):
        """
        Args:
            min_snr: Minimum SNR for acceptable cycles (default: 3.0)
            harmonic_tolerance: Tolerance for harmonic ratio matching (default: 0.15 = ±15%)
        """
        self.min_snr = min_snr
        self.harmonic_tolerance = harmonic_tolerance
        
        # Hurst's harmonic ratios: 2:1, 3:1, 4:1
        self.harmonic_ratios = [0.5, 0.333, 0.25, 2.0, 3.0, 4.0]
    
    def calculate_snr(self, prices, bandpass_signal, wavelength):
        """
        Calculate Signal-to-Noise Ratio using proper detrending.
        
        Args:
            prices: Original price data
            bandpass_signal: Extracted cycle (bandpass filtered)
            wavelength: Cycle wavelength in days
            
        Returns:
            dict with snr_linear, snr_db, quality label
        """
        # Detrend prices using Butterworth high-pass filter
        detrended = self._detrend_prices(prices)
        
        # Noise = detrended price - cycle signal
        noise = detrended - bandpass_signal
        
        # Calculate power
        cycle_power = np.var(bandpass_signal)
        noise_power = np.var(noise)
        
        # Avoid division by zero
        if noise_power == 0:
            snr_linear = 100.0
        else:
            snr_linear = cycle_power / noise_power
        
        snr_db = 10 * np.log10(snr_linear) if snr_linear > 0 else -100
        
        # Quality labels
        if snr_linear >= 5.0:
            quality = "High"
        elif snr_linear >= 3.0:
            quality = "Medium"
        elif snr_linear >= 2.0:
            quality = "Low"
        else:
            quality = "Poor"
        
        return {
            'snr_linear': float(snr_linear),
            'snr_db': float(snr_db),
            'quality': quality
        }
    
    def _detrend_prices(self, prices):
        """Remove trend from prices using Butterworth high-pass filter."""
        # Design high-pass filter (cutoff at 1/200 of signal length)
        nyquist = 0.5  # Assuming daily data, nyquist = 0.5 cycles/day
        cutoff_freq = 1.0 / 200.0  # Remove trends longer than 200 days
        normal_cutoff = cutoff_freq / nyquist
        
        # Clamp to valid range
        normal_cutoff = min(0.99, max(0.01, normal_cutoff))
        
        b, a = signal.butter(2, normal_cutoff, btype='high', analog=False)
        
        # Apply filter (pad to avoid edge effects)
        padded = np.pad(prices, (50, 50), mode='edge')
        filtered = signal.filtfilt(b, a, padded)
        detrended = filtered[50:-50]
        
        return detrended
    
    def find_harmonic_families(self, cycles_data):
        """
        Find cycles that are harmonically related (2:1, 3:1, 4:1 ratios).
        
        Args:
            cycles_data: List of cycle dicts with 'wavelength' key
            
        Returns:
            dict with 'families' (list of lists) and 'orphans' (list of wavelengths)
        """
        wavelengths = [c['wavelength'] for c in cycles_data]
        n = len(wavelengths)
        
        # Build adjacency graph
        adj = [set() for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                w1, w2 = wavelengths[i], wavelengths[j]
                ratio = w2 / w1 if w1 < w2 else w1 / w2
                
                # Check if ratio matches any harmonic ratio
                for harmonic_ratio in self.harmonic_ratios:
                    if abs(ratio - harmonic_ratio) / harmonic_ratio <= self.harmonic_tolerance:
                        adj[i].add(j)
                        adj[j].add(i)
                        break
        
        # Find connected components (families) using DFS
        visited = [False] * n
        families = []
        
        def dfs(node, family):
            visited[node] = True
            family.append(wavelengths[node])
            for neighbor in adj[node]:
                if not visited[neighbor]:
                    dfs(neighbor, family)
        
        for i in range(n):
            if not visited[i]:
                family = []
                dfs(i, family)
                families.append(sorted(family))
        
        # Identify orphans (single-member families)
        orphans = [f[0] for f in families if len(f) == 1]
        families = [f for f in families if len(f) > 1]
        
        return {
            'families': families,
            'orphans': orphans
        }
    
    def calculate_quality_score(self, snr_data, harmonic_data, wavelength):
        """
        Calculate overall quality score (0-100) and star rating (1-4 stars).
        
        Scoring:
        - SNR: 0-50 points
        - Harmonic family: 0-50 points
        
        Args:
            snr_data: dict from calculate_snr()
            harmonic_data: dict from find_harmonic_families()
            wavelength: cycle wavelength to score
            
        Returns:
            dict with score, stars, label, components
        """
        # SNR score (0-50 points)
        snr_linear = snr_data['snr_linear']
        if snr_linear >= 5.0:
            snr_score = 50
        elif snr_linear >= 3.0:
            snr_score = 40
        elif snr_linear >= 2.0:
            snr_score = 25
        else:
            snr_score = 10
        
        # Harmonic family score (0-50 points)
        is_orphan = wavelength in harmonic_data['orphans']
        num_partners = 0
        
        if not is_orphan:
            # Find which family this cycle belongs to
            for family in harmonic_data['families']:
                if wavelength in family:
                    num_partners = len(family) - 1  # Exclude self
                    break
        
        if num_partners >= 3:
            harmonic_score = 50  # Large family
        elif num_partners == 2:
            harmonic_score = 40  # Medium family
        elif num_partners == 1:
            harmonic_score = 25  # Small family
        else:
            harmonic_score = 0  # Orphan
        
        # Total score
        total_score = snr_score + harmonic_score
        
        # Convert to star rating
        if total_score >= 80:
            stars = 4
            label = "Excellent"
        elif total_score >= 60:
            stars = 3
            label = "Good"
        elif total_score >= 40:
            stars = 2
            label = "Fair"
        else:
            stars = 1
            label = "Poor"
        
        return {
            'score': int(total_score),
            'stars': stars,
            'label': label,
            'star_display': '⭐' * stars,
            'components': {
                'snr_score': snr_score,
                'harmonic_score': harmonic_score,
                'harmonic_partners': num_partners
            }
        }


# Standalone testing
if __name__ == "__main__":
    print("Testing Cycle Quality Analyzer...")
    
    # Mock data
    mock_cycles = [
        {'wavelength': 90},
        {'wavelength': 180},
        {'wavelength': 360},
        {'wavelength': 720},
        {'wavelength': 445},  # Orphan
        {'wavelength': 605},  # Orphan
    ]
    
    analyzer = CycleQualityAnalyzer(min_snr=2.0, harmonic_tolerance=0.15)
    
    # Find harmonic families
    families = analyzer.find_harmonic_families(mock_cycles)
    print(f"\nHarmonic Families: {families['families']}")
    print(f"Orphans: {families['orphans']}")
    
    # Mock SNR data
    for cycle in mock_cycles:
        wavelength = cycle['wavelength']
        
        # Mock SNR (higher for lower wavelengths in this example)
        if wavelength <= 180:
            snr = 6.0
        elif wavelength <= 360:
            snr = 4.5
        else:
            snr = 2.5
        
        snr_data = {'snr_linear': snr, 'snr_db': 10 * np.log10(snr), 'quality': 'Medium'}
        
        quality = analyzer.calculate_quality_score(snr_data, families, wavelength)
        
        print(f"\n{wavelength}d cycle:")
        print(f"  SNR: {snr:.1f}")
        print(f"  Star Rating: {quality['star_display']} ({quality['stars']} stars)")
        print(f"  Label: {quality['label']}")
        print(f"  Score: {quality['score']}/100")
        print(f"  Harmonic Partners: {quality['components']['harmonic_partners']}")
        print(f"  Is Orphan: {wavelength in families['orphans']}")
