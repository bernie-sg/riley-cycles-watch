# PDF Analysis Notes - SIGMA-L Algorithm

## PDF #06 Part 2 - Critical Findings

### Page 4-5: Morlet Wavelet Basics
- Uses Morlet wavelet (sinusoid × Gaussian)
- "Sinusoid of frequency equal to target mixed with gaussian function"
- Provides localization in time and frequency

### Page 6: **THE KEY INSIGHT**
**"We do this with our own analysis, changing the width of the Gaussian over frequencies to capture components in the most coherent way."**

SIGMA-L uses **ADAPTIVE Gaussian width** that changes based on frequency!

The composite bandpass filter image shows:
- Multiple wavelets with DIFFERENT widths
- Wider bandpass for detecting persistent cycles
- "The wider the bandpass, the more variation we can observe"

### Current Implementation Problem
Our code uses: `Q = 15.0 + 50.0 * freq`

This makes Q HIGHER for higher frequencies (narrower wavelets).
But SIGMA-L might use the OPPOSITE or a different relationship!

### For Wide Persistent Bands
Need LOWER Q (wider Gaussian) to create those wide horizontal bands in heatmap.

## Next: Find Exact Formula
Need to continue reading to find the exact Q factor formula SIGMA-L uses.

## PDF #06 Part 3 Analysis

### Page 9: Key Specification Found
Caption: "The peak is the 20 week component and has a width (frequency modulation) equivalent to around 43 days."

**Analysis of "43-day width":**
- 20 weeks = 140 days (center wavelength)
- Width = 43 days

Tested interpretations:
1. Q = 0.82 (assuming width = FWHM) → TOO WIDE/BLURRY
2. Q = 1.93 (assuming width = σ) → STILL TOO WIDE
3. Q = 3.0 + wavelength/100 (adaptive) → BETTER, shows 490d peak

**Current Status:**
- Adaptive Q showing improvement (490d peak detected)
- But still guessing at formula
- Need to continue reading PDF to find EXACT Q formula

### CRITICAL FINDING from PDF Page 9:
"The peak is the 20 week component and has a width (frequency modulation) equivalent to around 43 days."

**This is FREQUENCY MODULATION width (bandwidth in frequency domain), not time-domain width!**

For Morlet wavelet: **Q = center_wavelength / bandwidth_wavelength**

Q = 140 / 43 = **3.26**

This is the EXACT Q factor SIGMA-L uses!