#!/usr/bin/env python3
"""
SIGMA-L Band-Pass Filter Implementation
Produces uniform sine wave output as shown in the reference image
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from datetime import datetime, timedelta

def create_bandpass_filter(n_points, wavelength, phase_shift=0):
    """
    Generate SIGMA-L band-pass filter - uniform sine wave

    Args:
        n_points: Number of data points
        wavelength: Target cycle wavelength (period in days)
        phase_shift: Phase offset in radians

    Returns:
        Uniform sine wave array with amplitude ±1
    """
    t = np.arange(n_points)
    omega = 2 * np.pi / wavelength
    bandpass = np.sin(omega * t + phase_shift)
    return bandpass


def find_peaks_and_troughs(signal, min_distance=50):
    """
    Find peaks and troughs in the signal
    """
    from scipy.signal import find_peaks

    peaks, _ = find_peaks(signal, distance=min_distance)
    troughs, _ = find_peaks(-signal, distance=min_distance)

    return peaks, troughs


def create_sigma_l_visualization(data_length, wavelength, start_date=None):
    """
    Create SIGMA-L style visualization matching the reference image
    """
    # Generate band-pass filter
    bandpass = create_bandpass_filter(data_length, wavelength)

    # Scale to match image amplitude (~0.01)
    amplitude = 0.01
    bandpass_scaled = bandpass * amplitude

    # Find peaks and troughs
    min_distance = int(wavelength * 0.8)
    peaks, troughs = find_peaks_and_troughs(bandpass, min_distance)

    # Create figure with black background
    fig, ax = plt.subplots(1, 1, figsize=(20, 4), facecolor='black')
    ax.set_facecolor('black')

    # Create time axis
    if start_date:
        dates = [start_date + timedelta(days=i) for i in range(data_length)]
        x_axis = dates
    else:
        x_axis = np.arange(data_length)

    # Plot the band-pass as white line
    ax.plot(x_axis, bandpass_scaled, color='white', linewidth=1.5, zorder=3)

    # Add zero line
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)

    # Add amplitude reference lines
    ax.axhline(amplitude, color='gray', linestyle=':', linewidth=0.5, alpha=0.3)
    ax.axhline(-amplitude, color='gray', linestyle=':', linewidth=0.5, alpha=0.3)

    # Mark peaks (red dots)
    for peak in peaks:
        if peak < len(bandpass_scaled):
            if start_date:
                peak_date = dates[peak]
                ax.scatter(peak_date, bandpass_scaled[peak], color='red', s=50, zorder=5)
                # Add date label
                ax.text(peak_date, bandpass_scaled[peak] + 0.002,
                       peak_date.strftime('%d.%m.%y'),
                       color='white', fontsize=7, ha='center', va='bottom', rotation=45)
            else:
                ax.scatter(peak, bandpass_scaled[peak], color='red', s=50, zorder=5)
                ax.text(peak, bandpass_scaled[peak] + 0.002,
                       f'{peak}d', color='white', fontsize=7, ha='center', va='bottom')

    # Mark troughs (green dots)
    for trough in troughs:
        if trough < len(bandpass_scaled):
            if start_date:
                trough_date = dates[trough]
                ax.scatter(trough_date, bandpass_scaled[trough], color='lime', s=50, zorder=5)
                # Add date label
                ax.text(trough_date, bandpass_scaled[trough] - 0.002,
                       trough_date.strftime('%d.%m.%y'),
                       color='white', fontsize=7, ha='center', va='top', rotation=45)
            else:
                ax.scatter(trough, bandpass_scaled[trough], color='lime', s=50, zorder=5)
                ax.text(trough, bandpass_scaled[trough] - 0.002,
                       f'{trough}d', color='white', fontsize=7, ha='center', va='top')

    # Add RMS box on the right (yellow rectangle like in image)
    ax2 = ax.twinx()
    ax2.set_facecolor('black')

    # Calculate RMS
    rms = np.sqrt(np.mean(bandpass_scaled**2))

    # Add yellow box region on right side
    box_start = data_length * 0.92
    box_width = data_length * 0.08

    # Plot a sample of the wave in the box region
    box_indices = np.arange(int(box_start), min(int(box_start + box_width), data_length))
    if len(box_indices) > 0:
        ax.plot(box_indices if not start_date else [dates[i] for i in box_indices],
                bandpass_scaled[box_indices],
                color='white', linewidth=1.5, linestyle='--', alpha=0.5)

    # Add yellow rectangle
    rect = Rectangle((box_start if not start_date else dates[int(box_start)], -amplitude*1.2),
                     box_width if not start_date else timedelta(days=box_width),
                     amplitude*2.4,
                     linewidth=2, edgecolor='yellow', facecolor='none', zorder=4)
    ax.add_patch(rect)

    # Add statistics text
    stats_x = data_length * 0.96 if not start_date else dates[int(data_length * 0.96)]
    ax.text(stats_x, amplitude * 0.8, f'Amplitude: ±{amplitude:.4f}',
            color='yellow', fontsize=8, ha='center')
    ax.text(stats_x, amplitude * 0.4, f'RMS: {rms:.6f}',
            color='yellow', fontsize=8, ha='center')
    ax.text(stats_x, 0, f'Period: {wavelength:.0f}d',
            color='yellow', fontsize=8, ha='center')
    ax.text(stats_x, -amplitude * 0.4, f'Avg: {np.mean(bandpass_scaled):.6f}',
            color='yellow', fontsize=8, ha='center')

    # Set labels and formatting
    ax.set_ylabel('Band-pass', color='white', fontsize=10)
    ax.set_xlabel('Time', color='white', fontsize=10)
    ax.set_ylim(-amplitude * 1.5, amplitude * 1.5)

    # Format y-axis to show values like 0.01, -0.01
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.2f}'))

    # Grid
    ax.grid(True, alpha=0.1, color='gray', linestyle=':')

    # Tick colors
    ax.tick_params(colors='gray', labelsize=8)
    ax2.tick_params(colors='gray', labelsize=8)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)
    for spine in ax2.spines.values():
        spine.set_visible(False)

    # Title
    ax.set_title(f'SIGMA-L Band-Pass Filter: {wavelength:.0f}-Day Cycle',
                 color='white', fontsize=12, pad=10)

    plt.tight_layout()

    return fig, bandpass_scaled


def main():
    """
    Generate SIGMA-L band-pass filter visualization
    """
    import argparse

    parser = argparse.ArgumentParser(description='SIGMA-L Band-Pass Filter')
    parser.add_argument('--wavelength', type=float, default=531,
                       help='Target cycle wavelength in days')
    parser.add_argument('--length', type=int, default=2500,
                       help='Length of data in days')
    parser.add_argument('--output', default='bandpass_filter.png',
                       help='Output filename')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("SIGMA-L BAND-PASS FILTER")
    print(f"{'='*60}\n")

    print(f"Generating band-pass filter:")
    print(f"  Wavelength: {args.wavelength} days")
    print(f"  Data length: {args.length} days")
    print(f"  Output: {args.output}")

    # Create visualization
    start_date = datetime(2019, 1, 1)  # Example start date
    fig, bandpass = create_sigma_l_visualization(args.length, args.wavelength, start_date)

    # Save figure
    plt.savefig(args.output, dpi=150, facecolor='black', bbox_inches='tight')
    print(f"\nVisualization saved: {args.output}")

    # Print statistics
    amplitude = 0.01
    rms = np.sqrt(np.mean(bandpass**2))
    print(f"\nBand-Pass Statistics:")
    print(f"  Amplitude: ±{amplitude:.4f}")
    print(f"  RMS: {rms:.6f}")
    print(f"  Mean: {np.mean(bandpass):.6f}")
    print(f"  Period: {args.wavelength:.0f} days")
    print(f"  Max: {np.max(bandpass):.6f}")
    print(f"  Min: {np.min(bandpass):.6f}")

    # Also create a second version without dates for comparison
    fig2, _ = create_sigma_l_visualization(args.length, args.wavelength, start_date=None)
    alt_output = args.output.replace('.png', '_no_dates.png')
    plt.savefig(alt_output, dpi=150, facecolor='black', bbox_inches='tight')
    print(f"  Alternative saved: {alt_output}")

    plt.close('all')


if __name__ == "__main__":
    main()