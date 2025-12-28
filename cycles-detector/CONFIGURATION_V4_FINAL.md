# Cycles Detector V4 - Final Configuration

## Achievement
Successfully implemented sharp peak detection in power spectrum, matching SIGMA-L's visual style.

## Key Parameters

### Wavelet Configuration
- **Q Factor**: `Q = min(wavelength / 2.15, 300.0)`
  - 20x higher than PDF specification (42.94)
  - Produces extremely sharp, narrow wavelets
  - At 350d: Q ≈ 163
  - At 470d: Q ≈ 219

### Power Spectrum Display
- **Wavelength Range**: 100-800 trading days
- **Wavelength Step**: 5 trading days
- **Total Bars**: ~140 bars
- **Line Width**: 4 pixels

### High-Pass Filter (Optional)
- **600-day moving average** subtraction
- Controlled by "Suppress Long Cycles" checkbox (default: ON)
- Treats cycles >600d as "underlying trend"

### Color Mapping (8 levels)
- \>0.85: White (highest peaks)
- \>0.70: Yellow
- \>0.50: Orange (#ff9900)
- \>0.35: Orange-red (#ff6600)
- \>0.20: Pink (#cc3366)
- \>0.10: Purple (#7733aa)
- \>0.05: Dark purple (#442266)
- ≤0.05: Very dark (#221133)

## Current Results (TLT)
**Top Detected Cycles:**
1. 345 days (1.275 power)
2. 470 days (1.246 power)
3. 785 days (0.765 power)
4. 605 days (0.763 power)
5. 300 days (0.761 power)

## Visual Characteristics
- ✅ Sharp, distinct peaks (not rounded)
- ✅ Clear valleys between peaks
- ✅ Individual bars visible
- ✅ Good contrast between peaks/troughs
- ⚠️ Still needs further refinement to match SIGMA-L exactly

## Next Steps (V5)
- Fine-tune Q factor for even sharper peaks
- Adjust color thresholds for better peak prominence
- Test different wavelength steps (3-7 range)
- Match exact visual appearance of SIGMA-L sample

## Files Modified
- `algorithms/heatmap/heatmap_algo.py` - Q factor increased 20x
- `templates/index.html` - Color mapping improved, line width adjusted
- `app.py` - Added suppress_long_cycles parameter

Date: 2025-10-01
