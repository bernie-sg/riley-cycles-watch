# Heatmap Fix - V6 Implementation

## Date: 2025-10-02

## Problem Summary

V5's heatmap showed garbage instead of clean horizontal bands showing cycle persistence over time. The heatmap should show how peaks detected in the current power spectrum behave historically - do they persist (sticky cycles) or fade in/out.

## What V2 Did Right

V2's heatmap works correctly, showing:
- Clean, continuous horizontal bands for each cycle
- Consistent brightness across time
- Ability to see cycles building/fading in strength
- Proper time axis (past on left, current on right)

## What Was Broken in V5

### 1. **Wrong Time Rollback** (heatmap_algo.py line 78)
- **V5**: `rollback = week * 7` (7 calendar days)
- **WRONG**: Yahoo Finance data is trading days, not calendar days
- **Should be**: `rollback = week * 5` (5 trading days per week)
- **Impact**: Time axis completely misaligned, creates artifacts

### 2. **No Normalization** (heatmap_algo.py lines 123-125)
- **V5**: Returns raw absolute power values
- **Problem**: A cycle with power=2.5 today looks different brightness than power=2.5 six months ago
- **Should be**: Normalize each week's spectrum to max=1
- **Impact**: Inconsistent brightness, can't compare cycle strength across time

### 3. **Inconsistent Parameters**
- **Problem**: Different parameters used for current power spectrum vs heatmap history
- **Should be**: Same window_size, wavelength_range, wavelength_step for all weeks
- **Impact**: Peaks in current spectrum don't match bands in heatmap

## The Fix in V6

### Goal
Use V5's sharp peak detection algorithm (high Q, max power) for BOTH:
1. Current power spectrum (right side)
2. Historical heatmap (all columns going back in time)

This ensures the peaks you see NOW match the horizontal bands you see in HISTORY.

### Changes to heatmap_algo.py

#### 1. Fix Time Rollback (line 78)
```python
# BEFORE (V5):
rollback = week * 7  # WRONG - using calendar days

# AFTER (V6):
rollback = week * 5  # CORRECT - 5 trading days per week
```

#### 2. Add Normalization (after line 121)
```python
# BEFORE (V5):
return spectrum  # No normalization

# AFTER (V6):
# Normalize to max=1 for consistent brightness across time
max_val = np.max(spectrum)
if max_val > 0:
    spectrum /= max_val
return spectrum
```

#### 3. Keep V5's Algorithm for Peak Detection
- ✅ High Q factor: `Q = min(wavelength / 2.15, 300.0)`
- ✅ MAX power (not average)
- ✅ No smoothing (raw spectrum)
- ✅ Optional suppress_long_cycles filter

#### 4. Ensure Consistency
Every week in heatmap uses:
- Same `window_size` parameter (from UI slider, not hardcoded)
- Same `wavelengths` array
- Same Q factor formula
- Same power calculation method
- Same detrending approach
- Normalized to its own max=1

### Changes to app.py

Fixed heatmap calculation to balance window consistency with sufficient history:
```python
# BEFORE (V5 - broken):
heatmap_window = 4000  # Hardcoded
max_weeks = (len(self.prices) - heatmap_window) // 5

# AFTER (V6 - CRITICAL FIX):
# Cap window size to ensure we get desired years of history
# When user selects "Full Sample" (5689 bars), we can't go back 10 years
# Solution: Use smaller window for heatmap to get enough historical weeks

desired_weeks = min(heatmap_years * 52, 520)  # 10 years max
max_possible_window = len(self.prices) - (desired_weeks * 5)

# Use smaller of: user's window OR max that gives desired history
heatmap_window = min(window_size, max(max_possible_window, 2000))

max_weeks = (len(self.prices) - heatmap_window) // 5

for week in range(max_weeks):
    spectrum = process_week_on_grid(self.prices, week, wavelengths,
                                   window_size=heatmap_window,  # Use capped window
                                   suppress_long_cycles=suppress_long_cycles)
```

**Why This Fix?**
- With 5828 prices and window_size=5689 (full sample): max_weeks = 27 weeks (6 months only!)
- To show 10 years (520 weeks): need window ≤ 5828 - 2600 = 3228 bars
- Solution: Cap heatmap window to ensure we always get years of history
- Still uses same ALGORITHM (Q factor, wavelengths, etc.) - just different window SIZE

### Changes to templates/index.html

Fixed data array reversal for correct time axis:
```python
# BEFORE (V5):
const heatmapFlipped = data.heatmap.data[0].map((_, colIndex) =>
    data.heatmap.data.map(row => row[colIndex])
).map(row => row.reverse());  # Reverses time - WRONG

# AFTER (V6):
// Transpose only, no reverse - data already in correct order
const heatmapFlipped = data.heatmap.data[0].map((_, colIndex) =>
    data.heatmap.data.map(row => row[colIndex])
);
```

## Expected Result

After these changes, V6's heatmap should show:
1. **Clean horizontal bands** - each cycle appears as a continuous line across time
2. **Consistent brightness** - a cycle with relative power=1.0 looks the same brightness whether it's today or 2 years ago
3. **Correct time axis** - 2018 on left, 2024 on right
4. **Peak matching** - peaks in current power spectrum (right) match the horizontal bands in the heatmap
5. **Visible wobble** - can see cycles shifting in frequency over time (350d becoming 355d)
6. **Stickiness indicator** - persistent cycles show as unbroken bands, transient cycles fade in/out

## Testing Checklist

- [ ] Heatmap shows 6+ years of history (not just 6 months)
- [ ] Time axis: past on left, current on right
- [ ] Horizontal bands are continuous and smooth
- [ ] Current power spectrum peaks align with heatmap bands
- [ ] Brightness is consistent across all time periods
- [ ] No random white artifacts or vertical bands
- [ ] Can see cycles building/fading in strength over time
- [ ] Window size slider affects both power spectrum AND heatmap consistently

## Technical Notes

### Why Normalize Per Week?
Each week's spectrum is normalized to its own max=1 because:
- Absolute power values vary due to market volatility
- We care about RELATIVE cycle strength within each time period
- This makes brightness comparable across time
- Allows us to see if a cycle is getting stronger/weaker relative to other cycles

### Why 5 Days Per Week?
Yahoo Finance provides trading days only (Mon-Fri, excluding holidays):
- ~252 trading days per year
- ~5 trading days per week (average)
- Using 7 (calendar days) creates misalignment and artifacts

### Why Same Window Size?
Using consistent window_size across all time periods ensures:
- Same frequency resolution
- Same number of cycles visible
- Comparable results across time
- Peaks don't appear/disappear due to window length changes

## Previous Mistakes

1. **Tried to use V2's algorithm directly** - would have shown different peaks than V5's power spectrum
2. **Hardcoded 4000-bar window** - should use user's window_size parameter
3. **Reversed data array** - created time axis confusion
4. **Forgot normalization** - caused inconsistent brightness
5. **Used week*7 instead of week*5** - completely broke time alignment

## Success Criteria

V6 succeeds when:
1. User can see which cycles are "sticky" (persistent over years)
2. Heatmap peaks match current power spectrum peaks
3. Can visually identify when cycles are building/fading
4. Time axis makes sense (2018 → 2024)
5. No mysterious artifacts or white spots
