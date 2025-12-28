# SIGMA-L Scanner Algorithm Documentation

## Overview
The Scanner Clean algorithm implements SIGMA-L's cycle detection system using High-Q Morlet wavelets for precise frequency analysis. This matches the methodology described in PDF 02 about the Cycle Scanner.

## Core Components

### 1. High-Q Morlet Wavelets
From SIGMA_L_REVERSE_ENGINEERING.md and PDFs:
- **Formula**: `Q = 15.0 + 50.0 * freq`
- **Purpose**: Provides sharp frequency selectivity for precise cycle detection
- **Q Factor**: Higher Q = sharper frequency resolution (narrower bandwidth)
- **Implementation**: Complex Morlet wavelet with Gaussian envelope and sinusoidal carrier

### 2. Wavelet Convolution
Based on PDF methodology:
- Uses **complex Morlet wavelet convolution** across the price data
- Scans multiple wavelengths (30 to 1000 days)
- Computes power spectrum showing strength of each cycle
- RMS power calculation: `sqrt(total_power / count)`

### 3. Signal Processing Pipeline
1. **Data Preparation**:
   - Log transform of prices
   - Linear detrending to remove bias
   - Window of 2000 days for analysis

2. **Spectrum Computation**:
   - Scan wavelengths from 30 to 1000 days
   - Use 4-8 cycles per wavelet for good resolution
   - Step size of wavelength/8 for thorough scanning

3. **Noise Reduction**:
   - Median filter (window=3) to remove spike noise
   - Gaussian smoothing (window=10) for clean curves
   - Peak enhancement (factor=2.0) to highlight cycles
   - Adaptive smoothing in valleys to reduce noise

4. **Visualization**:
   - Creates interactive HTML chart
   - Shows power spectrum with identified peaks
   - Marks dominant cycles (531d, 260d, etc.)

## Key Algorithm Parameters

### Wavelet Parameters
```cpp
Q = 15.0 + 50.0 * freq  // Quality factor
sigma = Q / (2.0 * M_PI * freq)  // Gaussian width
cycles = min(8, max(4, n / wavelength))  // Cycles per wavelet
```

### Smoothing Parameters
- Median filter window: 3
- Gaussian smoothing window: 10
- Peak enhancement factor: 2.0
- Adaptive smoothing threshold: 0.3

### Scanning Range
- Minimum wavelength: 30 days
- Maximum wavelength: 1000 days
- Step size: 1 day (fine resolution)

## Output

The scanner produces:
1. **Power Spectrum**: Shows cycle strength at each wavelength
2. **Peak Detection**: Identifies dominant cycles
3. **HTML Visualization**: Interactive chart showing:
   - Wavelength on x-axis
   - Power/strength on y-axis
   - Labeled peaks for dominant cycles

## Relationship to SIGMA-L

This implementation matches SIGMA-L's scanner as described in PDF 02:
- **Fast detection** (<0.5 seconds for 4000 points)
- **Stripped convolution** for speed
- **Trading-critical information** retained
- **Multiple timeframes** supported

## Key Differences from Full SIGMA-L

1. **Simplified ranking**: No 0-1000 score calculation
2. **Basic visualization**: No heatmap/spectrogram
3. **Single instrument**: No composite analysis
4. **No phase tracking**: Just power spectrum

## Usage

Compile and run:
```bash
g++ -O3 -o scanner_clean scanner_clean.cpp
./scanner_clean
```

Opens HTML visualization showing detected cycles in the browser.