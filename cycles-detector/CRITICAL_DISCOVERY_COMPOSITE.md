# CRITICAL DISCOVERY: SIGMA-L Uses Composite Wavelets

## Date: 2025-09-30

## The Breakthrough

From PDF #06 Part 2, Page 6:

> **"We do this with our own analysis, changing the width of the Gaussian over frequencies to capture components in the most coherent way."**

The accompanying image shows **SIGMA-L uses a COMPOSITE BANDPASS FILTER** made from multiple wavelets with different Gaussian widths!

## What This Means

SIGMA-L is NOT using a single Q factor formula. Instead, they:

1. **Create multiple wavelets** with different Q values for each frequency
2. **Combine them into a composite filter** (shown as purple line in the PDF image)
3. This **captures components "in the most coherent way"**

This explains why we couldn't find a single Q formula - there isn't one! They use multiple Q values and combine results.

## The Image Evidence

The PDF shows their interface with multiple Gaussian envelopes of varying widths overlaid, creating a composite bandpass. The wider envelopes capture persistent cycles, narrower ones capture sharp transient cycles.

## Impact on Our Implementation

Our current approach uses a single Q value per wavelength. To match SIGMA-L exactly, we would need to:

1. Compute power using multiple Q values per wavelength
2. Combine the results (average? max? weighted?)
3. This would explain the "capture components in the most coherent way"

## Current Status

**What We Have Working:**
- ✅ Morlet wavelet convolution
- ✅ Adaptive Q with cap (Q = min(wavelength/42.94, 15))
- ✅ No smoothing (preserves sharp peaks)
- ✅ Percentile-based colormap scaling
- ✅ Wide persistent horizontal bands in heatmap
- ✅ Sharp peaks in power spectrum

**What's Still Different:**
- ❌ 700-day cycle dominance (vs SIGMA-L's 526-day)
- ❓ Single Q vs composite approach

## Next Steps

Options:
1. **Accept current approximation** - Our single adaptive Q is a reasonable approximation
2. **Implement composite approach** - Use multiple Q values and combine (more complex)
3. **Continue PDF reading** - Look for more details on the composite method

The composite approach would be more accurate but significantly more complex. Our current single adaptive Q might be "good enough" for practical use.