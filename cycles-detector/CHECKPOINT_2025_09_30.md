# CHECKPOINT - 2025-09-30

## Current Status
Working on fixing cycle detection to match SIGMA-L's detection of 500-526 day cycle band.

## Key Findings So Far

### Data Format
- **Source:** Yahoo Finance TLT data
- **Format:** TRADING DAYS (not calendar days)
- **Points:** 5828 trading days = ~23 years
- **SIGMA-L sample:** 5688 points (140 days difference, likely older data)

### The Problem
- **SIGMA-L detects:** Strong 495-545 day band (average 526) - dominant from 2010+
- **Our algorithm detects:** 726 day cycle as dominant, 526 shows only 0.54 power
- **Root cause:** Normalization issue - we normalize to max (1.0), which suppresses other cycles

### Test Results
Raw power values (no normalization):
- 500 days: 0.6692
- 526 days: 0.4290
- 726 days: 1.0456

After process_week_on_grid (with normalization):
- 526 days: 0.543
- 545 days: 1.000
- 726 days: 1.000

**Both 545 and 726 show 1.000 because of max normalization!**

### Current Algorithm Issues
1. **Normalization:** Lines 102-104 in heatmap_algo.py normalize to max value
2. **Post-processing:** apply_scanner_processing() may enhance peaks, suppress bands
3. **Q factor:** Q = 15.0 + 50.0 * freq might not match SIGMA-L

### Files Modified
- `/Users/bernie/Documents/Cycles Detector/Cycles Detector V4/webapp/app.py`
  - Changed default window_size to None (use full data)
  - Removed 1.451 trading/calendar conversion
  - Updated to use full 5828 sample
- `/Users/bernie/Documents/Cycles Detector/Cycles Detector V4/webapp/algorithms/heatmap/heatmap_algo.py`
  - Changed rollback to 7 days/week (was 5)
  - Removed calendar conversion
  - Updated comments

## Next Steps
1. Read PDF #06 carefully to understand SIGMA-L's exact algorithm
2. Fix normalization method
3. Verify 500-day cycle dominance in 2010-2020 window
4. Match SIGMA-L's heatmap visualization

## Webapp Status
- Running at http://localhost:5001
- Using corrected algorithm (full sample, no conversion)
- Still shows 726 as dominant due to normalization issue