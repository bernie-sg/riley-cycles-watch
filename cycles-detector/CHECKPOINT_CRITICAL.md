# CRITICAL CHECKPOINT - Must Find Exact Wavelet Parameters

## The Problem
Our heatmap shows cycles, but they are NOT wide persistent horizontal bands like SIGMA-L.

SIGMA-L shows:
- WIDE horizontal bands (like 166d in TSLA)
- Bands persist across ENTIRE timeline (years)
- Very bright, clear definition

Our output shows:
- Narrower features
- Less persistence
- Different appearance

## Root Cause
The wavelet Q factor and/or wavelet length calculation is WRONG.

Current code:
```python
Q = 15.0 + 50.0 * freq
cycles = min(8, max(4, n // wavelength))
wlen = min(n, wavelength * cycles)
```

This is clearly NOT matching SIGMA-L's approach.

## Next Step
MUST read PDF #06 carefully to find:
1. Exact Q factor formula
2. Exact wavelet length formula
3. Any other wavelet parameters

## Status
About to read PDF with extreme care to find these parameters.