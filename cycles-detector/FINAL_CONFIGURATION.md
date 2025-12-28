# Final Configuration - Cycle Detection Algorithm

## Key Discovery

SIGMA-L **limits the scan range** to suppress very long cycles (700-800d) which they treat as "underlying trend" rather than tradeable cycles. This is based on PDFs #04, #05, and #08.

## Current Configuration

### Wavelength Range
- **Min**: 100 trading days
- **Max**: 600 trading days (was 800)
- **Step**: 1 (for sharp peaks in visualization)
- **Rationale**: Excludes 700-800d "trend" cycles, focuses on tradeable mid-range cycles

### Q Factor
- **Formula**: `Q = min(wavelength / 42.94, 15.0)`
- **Rationale**: Based on PDF #06 Part 3 (140d cycle, 43d bandwidth)
- **Q at 525d**: ~12.2

### Processing
- **Smoothing**: None (raw spectrum)
- **Normalization**: None for heatmap data, percentile95 for display
- **Detrending**: Simple linear detrend after log transform

### Visualization
- **Frontend**: Thin vertical lines with spacing (sampleStep=3)
- **Line width**: 2px
- **Color mapping**: Amplitude-based (white/yellow/orange/pink/purple)

## Results with 100-600d Range

Detected peaks (trading days):
- 298d
- 257d
- 225d, 233d
- 218d
- 117-144d range

## Status

The algorithm correctly:
1. ✅ Suppresses 700-800d cycles by limiting scan range
2. ✅ Uses PDF-derived Q factor (42.94)
3. ✅ Shows individual sharp peaks in visualization
4. ✅ No artificial smoothing of spectrum

The fact that we're not detecting a dominant 525d peak suggests either:
1. The 525d cycle is not currently dominant in TLT (cycle evolution)
2. SIGMA-L screenshot shows a different time period
3. Additional preprocessing steps we haven't discovered yet

## Next Steps for User

1. Check if the webapp now shows results without the 740d dominance
2. Verify the power spectrum looks cleaner (no 760d peak)
3. The detected cycles (298d, 257d, 225d) are the actual dominant cycles in current TLT data with scan range 100-600d