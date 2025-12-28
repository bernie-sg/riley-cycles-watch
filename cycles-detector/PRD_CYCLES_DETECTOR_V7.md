# Product Requirements Document: Cycles Detector V7

## STATUS: DEVELOPMENT IN PROGRESS

## Changes from V6

### V7.0 (2025-10-03):
- Started from clean V6 codebase
- All V6 functionality preserved
- Ready for new feature development

---

## Inherited V6 Features

All features from V6 are included:
- ✓ Multi-symbol support (stocks, ETFs, futures)
- ✓ Auto-updating data via Yahoo Finance
- ✓ High-Q Morlet wavelet analysis
- ✓ Power spectrum with peak detection
- ✓ Time-frequency heatmap with global normalization
- ✓ Phase-optimized bandpass filter
- ✓ Pure sine wave projection
- ✓ Peak/trough timing signals

See `../Cycles Detector V6/webapp/PRD_CYCLES_DETECTOR_V6.md` for complete V6 documentation.

---

## Development Notes

V7 is a clean working copy for new development. V6 remains locked and unchanged for reference.

**Port**: 5001 (same as V6 - stop V6 before running V7)

**To Run**:
```bash
cd "/Users/bernie/Documents/Cycles Detector/Cycles Detector V7/webapp"
python3 app.py
```

**Access**: http://localhost:5001

---

*Document Version: 1.0*
*Last Updated: 2025-10-03*
*System: Cycles Detector V7*
*Status: DEVELOPMENT*
