# HEATMAP ALGORITHM - COMPLETE DOCUMENTATION

## OVERVIEW
The heatmap algorithm visualizes cycle persistence over time using the scanner_clean algorithm with a rolling window approach. It produces horizontal bands showing persistent cycles.

## THE CORE CONCEPT

### Fixed Grid System
The key to proper alignment is using a FIXED GRID from the start:

```python
# Define grid in trading days (what scanner uses)
trading_wavelengths = np.arange(100, 801, 5)  # 100-800 trading days

# Convert to calendar days for display
calendar_wavelengths = trading_wavelengths * 1.451

# Process all data directly on this grid
for week in weeks:
    spectrum = process_week_on_grid(prices, week, trading_wavelengths)
```

**NO INTERPOLATION** - Each week is processed to produce values at exactly these wavelengths.

## ALGORITHM PIPELINE

### 1. Weekly Rolling Window
```python
def process_week(prices, week, window_size=4000):
    rollback = week * 5  # 5 trading days per week
    end_idx = len(prices) - rollback
    start_idx = end_idx - window_size
```
- Window: 4000 trading days (constant)
- Rollback: 5 days per week
- Total: 260 weeks (5 years)

### 2. Scanner Processing (Per Week)
Each week's data goes through:
1. **Log transform**: `np.log(prices)`
2. **Linear detrending**: Remove trend line
3. **High-Q Morlet wavelet**: `Q = 15.0 + 50.0 * freq`
4. **Power computation**: RMS of convolution results
5. **Multi-stage smoothing**: Median → Gaussian → Peak enhance → Gaussian → Adaptive

### 3. Grid-Aligned Heatmap
```python
# Create matrix with fixed dimensions
heatmap = np.zeros((len(wavelengths), num_weeks))

# Fill without interpolation
for week in range(num_weeks):
    spectrum = process_week_on_grid(data, week, wavelengths)
    heatmap[:, week] = spectrum
```

### 4. Power Spectrum Calculation
**CRITICAL**: Use the most recent week's actual scanner output:
```python
# CORRECT - Use most recent scan
power_spectrum = heatmap[:, -1]  # Last column

# WRONG - Don't average
power_spectrum = np.mean(heatmap, axis=1)  # This causes misalignment
```

## IMPLEMENTATION FILES

### heatmap_algo.py
- Production implementation with fixed grid alignment
- Optimized for ~30 second runtime
- Coarse grid (step of 5) for speed while maintaining accuracy
- Processes 200 weeks of data
- Perfect alignment between heatmap and power spectrum

## KEY PARAMETERS

### Grid Resolution
- **Fine**: Step of 1-2 trading days (slow but precise)
- **Coarse**: Step of 5 trading days (fast, still good)
- **Too coarse**: Step > 10 (may miss peaks)

### Window Parameters
- **Window size**: 4000 trading days (don't change)
- **Rollback**: 5 trading days per week
- **Total weeks**: 260 for 5 years, 200 for faster processing

### Display Settings
- **Colormap**: Purple gradient (#000000 → #ffffff)
- **Threshold**: 15% of max for visibility
- **vmax**: 80% of max for contrast

## ALIGNMENT FIXES

### Problem 1: Interpolation Shifts
**Issue**: Interpolating spectra onto a master grid shifts peak positions
**Solution**: Process directly on fixed grid, no interpolation

### Problem 2: Averaged Power Spectrum
**Issue**: Averaging across weeks blurs peaks
**Solution**: Use most recent week's spectrum for power display

### Problem 3: Grid Mismatch
**Issue**: Heatmap and power spectrum use different Y-axes
**Solution**: Both use exact same wavelength array:
```python
# SAME grid for both
ax1.imshow(heatmap, extent=[0, weeks, wavelengths[0], wavelengths[-1]])
ax2.barh(wavelengths, power_spectrum)
ax2.set_ylim(wavelengths[0], wavelengths[-1])  # EXACT same limits
```

## COMMON MISTAKES TO AVOID

### 1. Variable Grid
```python
# WRONG - Different grid each week
for week in weeks:
    wavelengths = compute_wavelengths(week)  # Changes each time

# CORRECT - Fixed grid
fixed_wavelengths = np.arange(100, 801, 5)
for week in weeks:
    spectrum = process_on_grid(data, fixed_wavelengths)
```

### 2. Interpolation After Processing
```python
# WRONG - Process then interpolate
spectrum = scanner_clean(data)
interpolated = np.interp(master_grid, spectrum_wavelengths, spectrum)

# CORRECT - Process directly on target grid
spectrum = process_on_grid(data, master_grid)
```

### 3. Wrong Power Source
```python
# WRONG - Average of interpolated heatmap
power = np.mean(heatmap, axis=1)

# CORRECT - Most recent actual scan
power = process_week_on_grid(prices, 0, wavelengths)  # Week 0 = now
```

## EXPECTED RESULTS

For TLT, you should see:
- **531d cycle**: Strong persistent band
- **691d cycle**: Usually visible
- **321d & 429d cycles**: Medium strength
- **Clean horizontal bands** (not patchy/noisy)
- **Perfect alignment** between heatmap bands and power spectrum peaks

## PYTHON vs C++ COMPARISON

### Python (Working)
- ✅ Produces results reliably
- ✅ Easy to debug and modify
- ❌ Slower (30s - 2min)
- ❌ May timeout on full resolution

### C++ (generate_weekly_scanners.cpp)
- ✅ Much faster execution
- ✅ Can handle full resolution
- ❌ Often produces black/empty output (unknown issue)
- ❌ Harder to debug

**Recommendation**: Use Python with coarse grid for development, C++ for production if output issue can be resolved.

## HOW TO RUN

```bash
cd "/Users/bernie/Documents/Cycles Detector"
python3 algorithms/heatmap/heatmap_algo.py
open heatmap_algo_fast.png
```

## VALIDATION CHECKLIST

✓ Horizontal bands are clean and persistent
✓ Power spectrum peaks align with heatmap bands
✓ 531d cycle is clearly visible
✓ No patchy/noisy artifacts
✓ Grid lines match between plots
✓ Y-axis has same range for both plots

## STATUS

**WORKING** - The fixed grid approach solves alignment issues while maintaining the exact scanner_clean algorithm. The fast version runs reliably in ~30 seconds.

---

Created: 2024-09-27
Algorithm Status: COMPLETE WITH ALIGNMENT FIXED
Based on: scanner_clean algorithm with rolling window