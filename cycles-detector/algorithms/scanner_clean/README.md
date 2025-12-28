# SCANNER_CLEAN - QUICK REFERENCE

## THE MAGIC FORMULA

**High-Q Morlet Wavelet:**
```cpp
Q = 15.0 + 50.0 * freq
```

This is THE formula that makes everything work. DO NOT CHANGE.

## To Build & Run:

### Best Implementation (Heatmap):
```bash
g++ -O3 -o generate_weekly_scanners generate_weekly_scanners.cpp
./generate_weekly_scanners
open weekly_heatmap.html
```

### Basic Scanner:
```bash
g++ -O3 -o scanner_clean scanner_clean.cpp
./scanner_clean
```

## Files:
- `scanner_clean.cpp` - Core algorithm
- `generate_weekly_scanners.cpp` - BEST heatmap generator
- `simple_heatmap_fixed.cpp` - Alternative heatmap
- `SCANNER_CLEAN_COMPLETE_DOCUMENTATION.md` - Full details

## Key Processing Pipeline:
1. Log transform prices
2. Linear detrend
3. Apply High-Q Morlet wavelet
4. Calculate RMS power (not average!)
5. Multi-stage smoothing:
   - Median filter (3)
   - Gaussian smooth (10)
   - Peak enhancement (2x)
   - Gaussian smooth (5)
   - Adaptive smooth (threshold 0.3)

## Critical Parameters:
- Wavelength range: 100-800 days
- Window size: 4000 bars
- Wavelet cycles: 4-8 (adaptive)
- Step size: wavelength/8

## Expected Results for TLT:
- 531d cycle (strongest)
- 260d cycle
- 180d cycle
- Clean horizontal bands in heatmap

**Status**: WORKING PERFECTLY - DO NOT MODIFY