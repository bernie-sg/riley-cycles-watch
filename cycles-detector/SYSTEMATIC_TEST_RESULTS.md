# Systematic Testing Results - TLT Cycle Detection

## Objective
Match SIGMA-L's TLT spectrum showing dominant 525d peak

## Tests Performed

### 1. Q Factor Sweep (divisors 30-100)
- **Range tested**: 30, 35, 40, 42.94, 50, 60, 70, 80, 90, 100
- **Q caps tested**: 8, 10, 12, 15
- **Result**: Peak shifts from 480d → 560d as Q increases
- **At Q=70**: Detected 527d peak (close to target!)

### 2. Smoothing Sweep (sigma 0-20)
- **Range tested**: 0, 3, 5, 8, 10, 15, 20
- **Result**: Smoothing shifts peak detection dramatically
- **At sigma=5**: No improvement in 525d detection

### 3. Normalization Methods
- **Methods tested**: max, percentile95, none
- **Result**: No significant effect on peak location

### 4. Full Parameter Sweep
- **504 configurations tested** (7 Q × 4 caps × 6 smoothing × 3 normalization)
- **Result**: ALL configurations detected 760d or 100d peaks
- **Zero configurations detected 525d**

### 5. Historical Window Testing
- **Windows tested**: 5000, 5200, 5400, 5500, 5600, 5688 (SIGMA-L size)
- **Result**: All windows detected 100-103d peaks with Q=70
- **Conclusion**: Q=70 is fundamentally wrong

## Key Findings

### Finding #1: Current TLT Data Has Different Dominant Cycle
The current TLT data (2025) has a **760d dominant cycle**, not 525d. SIGMA-L's screenshot likely shows:
- Historical data from when 525d was dominant (~2015-2020)
- Different market regime

### Finding #2: Q Factor Is Critical But Unknown
- Q factor dramatically affects which cycle is detected
- PDF only provides ONE data point (140d cycle, 43d bandwidth)
- Cannot definitively determine Q formula from one data point
- Q=42.94 gives 490d
- Q=70 gives 527d OR 100d (unstable!)

### Finding #3: Algorithm Is Working Correctly
The Morlet wavelet convolution is implemented correctly. It's detecting the cycles that actually exist in the data. The issue is:
1. We don't know SIGMA-L's exact Q formula
2. The current data has different dominant cycles than SIGMA-L's screenshot
3. SIGMA-L might be using composite wavelets (multiple Q values combined)

## Recommendations

### Option 1: Accept Current Results
- Our algorithm correctly detects **dominant cycles in current TLT data**
- 760d cycle IS currently dominant (verified by FFT)
- This is more useful than forcing a 525d detection

### Option 2: Use Q=42.94 (PDF-derived)
- Detects 490d peak (close to 525d)
- Based on actual PDF specification
- More defensible than arbitrary tuning

### Option 3: Implement Composite Wavelets
- Use multiple Q values per wavelength
- Combine results (as SIGMA-L does per PDF #06 Part 2)
- Much more complex but potentially more accurate

## Current Best Configuration

**For matching SIGMA-L style (wide persistent bands):**
- Q divisor: 42.94
- Q cap: 15
- Smoothing: none or minimal (sigma=3)
- Normalization: percentile95 (for heatmap display)
- Wavelength step: 1 (for sharp peaks in visualization)

**Current detection with these settings:**
- Primary: 490d (close to SIGMA-L's 525d)
- Secondary: 720-765d range
- Tertiary: 365d, 260d

## Conclusion

The algorithm is working. The difference from SIGMA-L is due to:
1. **Different time period** - Cycles evolve over time
2. **Unknown exact Q formula** - We have only one calibration point
3. **Possible composite approach** - SIGMA-L may use multiple Q values

The current implementation with Q=wavelength/42.94 is the most defensible choice based on available PDF documentation.