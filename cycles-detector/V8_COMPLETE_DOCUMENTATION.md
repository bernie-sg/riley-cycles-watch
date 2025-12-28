# CYCLES DETECTOR V8 - COMPLETE DOCUMENTATION
**Date:** October 2025
**Status:** Stable Release
**Purpose:** Interactive web-based SIGMA-L cycle analysis system

---

## TABLE OF CONTENTS
1. [Overview](#overview)
2. [Current Scanning Algorithm](#current-scanning-algorithm)
3. [Core Features](#core-features)
4. [Architecture](#architecture)
5. [API Reference](#api-reference)
6. [Configuration Parameters](#configuration-parameters)
7. [Known Issues & Limitations](#known-issues--limitations)
8. [Algorithm Documentation](#algorithm-documentation)
9. [Development Guide](#development-guide)

---

## OVERVIEW

Cycles Detector V8 is a complete web-based implementation of the SIGMA-L cycle analysis methodology. It provides real-time, interactive visualization of market cycles through power spectrum analysis, heatmap visualization, and bandpass filtering.

### Key Capabilities
- **Multi-symbol Support:** TLT, SPY, NVDA, MSFT, TSLA, and more
- **Real-time Analysis:** Sub-second response for parameter changes
- **Interactive Charts:** Plotly.js-based visualizations with zoom, pan, hover
- **Configurable Windows:** Analyze from 1000 to 5000 bars of historical data
- **Wavelength Scanning:** Detect cycles from 100 to 1200 calendar days

### Technology Stack
- **Backend:** Python 3, Flask
- **Frontend:** HTML5, JavaScript, Plotly.js
- **Algorithms:** NumPy, SciPy (Morlet wavelets, FFT, signal processing)
- **Data:** Text files (prices) loaded at startup

---

## CURRENT SCANNING ALGORITHM

### Morlet Wavelet Transform (Primary Algorithm)

**Location:** `algorithms/heatmap/heatmap_algo.py:80-144`
**Function:** `process_week_on_grid()`

#### Algorithm Details

The current cycle detection algorithm uses **Morlet Wavelet Transform** with adaptive Q-factor:

```python
# Core wavelet creation (line 13-29)
def create_high_q_morlet(freq, length):
    """Morlet wavelet with INVERTED adaptive Q for sharp bands"""
    # INVERTED: Higher Q for LOWER frequencies (longer wavelengths)
    Q = 50.0 - 45.0 * freq  # Decreases from ~50 to ~5 as freq increases
    Q = max(Q, 3.0)  # Floor to prevent too-narrow bandwidth
    sigma = Q / (2.0 * np.pi * freq)

    t = np.arange(length) - length/2.0
    envelope = np.exp(-t**2 / (2.0 * sigma**2))
    carrier = np.exp(1j * 2.0 * np.pi * freq * t)
    wavelet = envelope * carrier

    norm = np.sqrt(np.sum(np.abs(wavelet)**2))
    wavelet /= norm

    return wavelet
```

#### Processing Steps

1. **Data Preprocessing** (lines 104-111)
   - Extract price window based on rollback weeks
   - Handle negative prices (shift to positive range)
   - Apply log transformation: `data = np.log(price_window)`

2. **Optional High-Pass Filter** (lines 114-124)
   - Suppresses long-term cycles above 600 days
   - Uses moving average subtraction
   - Configurable via `suppress_long_cycles` parameter

3. **Linear Detrending** (lines 126-130)
   - Removes linear trend using `np.polyfit()`
   - Ensures stationarity for wavelet analysis

4. **Wavelet Power Computation** (line 133)
   ```python
   spectrum = np.array([compute_power(data, wl) for wl in trading_wavelengths])
   ```

5. **Post-Processing** (lines 59-78)
   - Median filtering (3-point window)
   - Smoothing (5-point convolution)
   - Peak enhancement (doubles above-mean values)

#### Key Parameters

| Parameter | Default | Range | Purpose |
|-----------|---------|-------|---------|
| `window_size` | 4000 | 1000-5000 | Historical data window |
| `min_wavelength` | 100 | 50-500 | Minimum cycle (trading days) |
| `max_wavelength` | 800 | 200-1200 | Maximum cycle (trading days) |
| `wavelength_step` | 5 | 1-20 | Scanning resolution |

#### Algorithm Characteristics

**Strengths:**
- Excellent frequency resolution for long cycles (>300 days)
- Adaptive Q-factor provides sharp, distinct bands in heatmap
- Robust to noise through post-processing filters
- Fast execution (~0.5-2 seconds for full scan)

**Weaknesses:**
- Lower Q for short cycles (<150 days) reduces sharpness
- High-pass filter can suppress very long cycles (>600 days)
- Requires detrending (may miss trending markets)

---

## CORE FEATURES

### 1. Power Spectrum Analysis

**File:** `app.py:120-185`
**Endpoint:** `/api/analyze`

Detects dominant market cycles using Morlet wavelet convolution:

```python
# Scan across wavelength range
for wavelength in trading_wavelengths:
    power = compute_power(detrended_data, wavelength)
    spectrum.append(power)
```

**Output:**
- List of wavelengths (calendar days)
- Corresponding power values (normalized 0-1)
- Top 5 peaks ranked by power

### 2. Interactive Heatmap

**Algorithm:** `algorithms/heatmap/heatmap_algo.py:146-262`

Visualizes cycle strength evolution over time (rolling window analysis):

- **Horizontal Axis:** Time (weeks ago, rolling backward)
- **Vertical Axis:** Wavelength (100-800 trading days)
- **Color Intensity:** Cycle power (purple gradient, 0-1)
- **Coverage:** Configurable years (1-5 years)

**Processing:**
- Processes every 2nd week for speed (configurable via `week_step`)
- Uses same Morlet wavelet algorithm as power spectrum
- Global normalization option for cross-period comparison

### 3. Bandpass Filter Generation

**File:** `algorithms/bandpass/wavelet_bandpass.py`

Generates bandpass-filtered signals for specific wavelengths:

```python
def generate_bandpass(prices, wavelength, phase_shift=0):
    """
    Generate bandpass signal using Morlet wavelet convolution

    Returns:
        bandpass_signal: Oscillating signal around 0
        phase_aligned: Signal phase-aligned to price peaks/troughs
    """
```

**Features:**
- Automatic phase detection via cross-correlation
- Peak/trough marking on bandpass and price charts
- Future projection (2.5 cycles forward)
- Smart amplitude scaling (matches price swing range)

### 4. Cycle Rating System

**File:** `algorithms/cycle_rating.py:180-257`

Implements Sigma-L A/B/C/D classification:

| Rating | Criteria | Description |
|--------|----------|-------------|
| A | amp_stat>0.8, freq_stat>0.8, gain_rank=1, isolation>0.7, SNR>5 | WOW! Beacon-like quality |
| B | amp_stat>0.7, freq_stat>0.7, gain_rank≤2, isolation>0.6, SNR>3 | Excellent, clear signal |
| C | amp_stat>0.6, freq_stat>0.6, gain_rank≤2, SNR>2 | Good, moderate quality |
| D | Below C thresholds | Weak, high modulation |

**Metrics Calculated:**
- Amplitude stationarity (0-1)
- Frequency stationarity (0-1)
- Spectral isolation (0-1)
- Signal-to-noise ratio
- Gain rank (1st, 2nd, or 3rd strongest peak)

### 5. Component Yield Calculation

**File:** `algorithms/component_yield.py:13-94`

Simulates perfect trading of a specific cycle:

```python
def calculate_component_yield(bandpass_signal, prices, wavelength):
    """
    Calculate theoretical trading performance

    Strategy: Buy at troughs, sell at peaks
    Returns:
        - yield_percent: Cumulative return %
        - num_trades: Number of complete cycles
        - trades: List of entry/exit details
    """
```

**Yield Ratings:**
- **A/B:** ≥100% yield (Excellent)
- **C:** 50-100% yield (Good)
- **D:** <50% yield (Weak)

---

## ARCHITECTURE

### Directory Structure

```
Cycles Detector V8/
└── webapp/
    ├── app.py                      # Flask backend (main application)
    ├── templates/
    │   └── index.html              # Frontend interface
    ├── algorithms/
    │   ├── heatmap/
    │   │   ├── heatmap_algo.py     # Morlet wavelet heatmap
    │   │   └── README.md
    │   ├── bandpass/
    │   │   ├── wavelet_bandpass.py # Bandpass generation
    │   │   ├── sigma_l_bandpass_filter.py  # Simple sine wave (visualization)
    │   │   ├── BANDPASS_COMPLETE_DOCUMENTATION.md
    │   │   └── README.md
    │   ├── scanner_clean/          # Historical scanner algorithm
    │   │   ├── SCANNER_CLEAN_COMPLETE_DOCUMENTATION.md
    │   │   └── README.md
    │   ├── cycle_rating.py         # A/B/C/D classification
    │   └── component_yield.py      # Trading yield calculation
    ├── *.txt                       # Price data files (TLT, SPY, NVDA, etc.)
    ├── README.md                   # Quick start guide
    ├── V8_COMPLETE_DOCUMENTATION.md  # This file
    ├── PRD_CYCLES_DETECTOR_V7.md   # Product requirements
    ├── FINAL_CONFIGURATION.md      # Configuration notes
    └── test_*.py                   # Various test scripts
```

### Data Flow

```
User Browser
    ↓ (HTTP GET /api/analyze?params)
Flask Backend (app.py)
    ↓ Load price data
    ↓ Call process_week_on_grid()
Morlet Wavelet Algorithm (heatmap_algo.py)
    ↓ Compute power spectrum
    ↓ Generate heatmap
    ↓ Apply scanner processing
    ↓ Return spectrum + heatmap
Bandpass Generation (wavelet_bandpass.py)
    ↓ Convolve with Morlet wavelet
    ↓ Detect phase via cross-correlation
    ↓ Generate future projection
    ↓ Return bandpass + phase info
Flask Backend
    ↓ Package as JSON
User Browser
    ↓ Plotly.js renders charts
```

### State Management

**Backend:** Stateless (each request is independent)
- Price data loaded once at startup
- No session management
- All parameters passed via query string

**Frontend:** JavaScript variables
- Current configuration stored in `<input>` values
- Charts rebuilt on each API response
- No persistence (reload resets to defaults)

---

## API REFERENCE

### GET /api/analyze

**Purpose:** Run full cycle analysis with specified parameters

**Query Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `symbol` | string | "TLT" | Any loaded symbol | Stock/ETF ticker |
| `window_size` | int | 4000 | 1000-5000 | Historical bars to analyze |
| `min_wavelength` | int | 100 | 50-500 | Minimum cycle (trading days) |
| `max_wavelength` | int | 800 | 200-1200 | Maximum cycle (trading days) |
| `wavelength_step` | int | 5 | 1-20 | Scanning resolution |
| `phase_method` | string | "cross_corr" | cross_corr, peaks | Phase detection method |
| `phase_window_size` | int | - | - | (Not currently used) |
| `heatmap_years` | float | 4.0 | 1.0-10.0 | Heatmap time coverage |
| `suppress_long_cycles` | bool | true | true/false | Apply high-pass filter |
| `align_to_troughs` | bool | false | true/false | ⚠️ NOT IMPLEMENTED (UI only) |
| `price_chart_years` | float | 10.0 | 1.0-20.0 | Price chart coverage |

**Response Format:**

```json
{
  "power_spectrum": {
    "wavelengths": [100, 105, 110, ...],  // Calendar days
    "spectrum": [0.23, 0.45, 0.67, ...],  // Power values (0-1)
    "top_peaks": [
      {"wavelength": 630, "power": 0.95},
      {"wavelength": 350, "power": 0.87},
      ...
    ]
  },
  "heatmap": {
    "heatmap_data": [[...], [...], ...],  // 2D array [wavelength][time]
    "heatmap_weeks": 208,
    "heatmap_wavelengths": [100, 105, ...]
  },
  "bandpass": {
    "wavelength": 630,
    "bandpass_signal": [...],
    "phase_shift": 1.57,
    "peaks": [120, 390, 660, ...],
    "troughs": [255, 525, 795, ...],
    "historical_length": 4000,
    "future_projection": [...]
  },
  "price_data": {
    "dates": ["2020-01-01", "2020-01-02", ...],
    "prices": [145.2, 145.8, ...]
  },
  "cycle_rating": {
    "class": "A",
    "score": 92.5,
    "amp_stationarity": 0.85,
    "freq_stationarity": 0.82,
    "spectral_isolation": 0.78,
    "snr": 6.2,
    "gain_rank": 1
  },
  "component_yield": {
    "yield_percent": 127.5,
    "num_trades": 12,
    "trades": [...]
  }
}
```

### GET /api/config

**Purpose:** Get configuration options and available data

**Response:**

```json
{
  "symbols": ["TLT", "SPY", "NVDA", "MSFT", "TSLA"],
  "total_data_points": 5828,
  "date_range": {
    "start": "2001-07-26",
    "end": "2025-10-05"
  }
}
```

---

## CONFIGURATION PARAMETERS

### Window Size (Historical Data)

| Value | Coverage | Heatmap Years | Best For |
|-------|----------|---------------|----------|
| 1000 | ~7.4 years | ~15 years | Quick scans, recent cycles |
| 2000 | ~14.7 years | ~8 years | Short-term analysis |
| **4000** | **~29.5 years** | **~4 years** | **Standard (recommended)** |
| 5000 | ~36.9 years | ~3 years | Long-term validation |

**Trade-off:** Larger windows = more data for stable detection, but shorter heatmap coverage.

### Wavelength Range

| Setting | Min/Max (trading days) | Calendar Days | Cycles Detected |
|---------|------------------------|---------------|-----------------|
| Short cycles | 50-200 | 72-290 | Quarterly, semi-annual |
| **Standard** | **100-800** | **145-1160** | **6mo to 3yr cycles** |
| Long cycles | 200-1200 | 290-1740 | Multi-year cycles |

**Trade-off:** Wider range = more cycles detected, but slower processing.

### Wavelength Step

| Value | Grid Points | Speed | Resolution |
|-------|-------------|-------|------------|
| 1 | 700 | Slow | Very fine |
| **5** | **140** | **Fast** | **Standard** |
| 10 | 70 | Very fast | Coarse |
| 20 | 35 | Instant | Rough |

**Trade-off:** Smaller steps = better precision, but longer compute time.

---

## KNOWN ISSUES & LIMITATIONS

### ⚠️ CRITICAL: align_to_troughs Not Implemented

**Issue:** The UI checkbox "Align Phase to Lows" (`alignToTroughs`) exists on the configuration panel (index.html:340-343), and the parameter is passed through the entire stack, but **it is NOT actually used in any algorithm**.

**Status:** Documented as future feature (not a bug, intentional deferral)

**Location in Code:**
- **Frontend:** `index.html:340-343` (checkbox)
- **Frontend JS:** `index.html:520` (parameter passed to API)
- **Backend:** `app.py:646` (received but ignored)
- **Passed to:** `app.py:670` (analyze() function)
- **Not used in:** Any algorithm file (bandpass, heatmap, etc.)

**Expected Behavior (if implemented):**
When `align_to_troughs = true`, the bandpass filter should invert or phase-shift by 180° so that bandpass troughs align with price lows (instead of peaks aligning with price highs).

**Workaround:**
Manually inspect both the standard and inverted signals. To implement, modify `wavelet_bandpass.py` to add phase shift of π (3.14159) when this parameter is True.

**Planned Fix:** V9 (future version)

---

### Other Limitations

#### 1. Symbol Changes Require Restart

**Issue:** Changing symbols via dropdown works, but cached data may cause issues.

**Workaround:** Restart Flask server when switching symbols frequently.

#### 2. Very Short Wavelengths (<100 days) Have Low Accuracy

**Cause:** Morlet wavelet Q-factor drops for high frequencies (short cycles).

**Workaround:** Use min_wavelength ≥ 100 for reliable results.

#### 3. Future Projection May Diverge

**Issue:** Bandpass future projection (2.5 cycles) assumes cycle continues unchanged.

**Limitation:** Real market cycles degrade, modulate, or disappear over time.

**Interpretation:** Use projections as "if this cycle continues perfectly" scenarios, not predictions.

#### 4. No Real-time Data Updates

**Issue:** Price data is loaded at startup from static text files.

**Workaround:** Periodically update `.txt` files and restart server.

**Future:** Add API integration (Yahoo Finance, Alpaca, etc.)

#### 5. Heatmap Normalization Can Be Misleading

**Issue:** Default normalization is per-week (max=1.0 for each column).

**Effect:** Weak cycles in low-power periods may appear strong.

**Workaround:** Use global normalization option (pass `normalize=False` and normalize across all weeks).

---

## ALGORITHM DOCUMENTATION

### Detailed Algorithm References

For in-depth algorithm documentation, see:

1. **Heatmap Algorithm (Morlet Wavelet):**
   - `algorithms/heatmap/heatmap_algo.py` (code)
   - Lines 13-29: Wavelet creation
   - Lines 80-144: Main processing function
   - Lines 146-262: Visualization generation

2. **Bandpass Generation:**
   - `algorithms/bandpass/BANDPASS_COMPLETE_DOCUMENTATION.md`
   - Covers wavelet convolution, phase detection, future projection

3. **Cycle Rating:**
   - `algorithms/cycle_rating.py`
   - See function `rate_cycle()` (lines 180-257)
   - Metrics: amplitude/frequency stationarity, SNR, isolation

4. **Component Yield:**
   - `algorithms/component_yield.py`
   - See `calculate_component_yield()` (lines 13-94)
   - Trading simulation, yield calculation

### Historical Context

**scanner_clean Algorithm** (deprecated in V8):
- Previous CWT-based scanning algorithm
- Documented in `algorithms/scanner_clean/SCANNER_CLEAN_COMPLETE_DOCUMENTATION.md`
- Replaced by faster Morlet wavelet approach in heatmap_algo.py

---

## DEVELOPMENT GUIDE

### Running the Application

```bash
# Install dependencies
pip3 install flask numpy scipy matplotlib plotly

# Navigate to webapp directory
cd "/Users/bernie/Documents/Cycles Detector/Cycles Detector V8/webapp"

# Start Flask server
python3 app.py

# Access in browser
http://localhost:5001
```

### Adding a New Symbol

1. Download price data (CSV format, Date,Close columns)
2. Extract close prices to text file:
   ```python
   import pandas as pd
   df = pd.read_csv('symbol_data.csv')
   np.savetxt('symbol_prices.txt', df['Close'].values)
   ```
3. Place file in webapp/ directory (e.g., `aapl_prices.txt`)
4. Restart Flask server
5. Symbol will auto-appear in dropdown

### Modifying the Algorithm

**To change scanning algorithm:**

1. Edit `algorithms/heatmap/heatmap_algo.py`
2. Modify `create_high_q_morlet()` for different wavelet
3. Or replace `compute_power()` entirely with new method
4. Restart Flask server (Python caches modules)

**To add Bartels algorithm (V9 plan):**

1. Create `algorithms/heatmap/bartels_algo.py`
2. Implement `process_week_bartels()` function
3. Add dropdown to `index.html` for algorithm selection
4. Modify `app.py` to call correct algorithm based on parameter

### Testing Changes

**Unit Tests:**
```bash
# Test wavelet generation
python3 algorithms/heatmap/test_wavelet.py

# Test bandpass filter
python3 algorithms/bandpass/test_wavelet_on_tlt.py

# Test phase detection
python3 algorithms/bandpass/test_phase_issue.py
```

**Full Integration Test:**
```bash
# Run Flask app
python3 app.py

# In another terminal, test API
curl "http://localhost:5001/api/analyze?symbol=TLT&window_size=4000"
```

---

## VERSION HISTORY

### V8 (Current)
- **Released:** October 2025
- **Algorithm:** Morlet Wavelet Transform
- **Key Features:**
  - Multi-symbol support (TLT, SPY, NVDA, MSFT, TSLA)
  - Interactive heatmap with purple colormap
  - Cycle rating system (A/B/C/D)
  - Component yield calculation
  - Future projection (2.5 cycles)
  - Configurable parameters (window, wavelength, step)
- **Known Issues:**
  - align_to_troughs checkbox not implemented

### V7
- Improved bandpass phase detection
- Added smart amplitude scaling
- Optimized heatmap processing

### V6
- Fixed heatmap grid alignment
- Added global normalization option

### Earlier Versions
- See `PRD_CYCLES_DETECTOR_V7.md` for V7 requirements
- See `PRD_CYCLES_DETECTOR_V6.md` for V6 requirements

---

## FUTURE ROADMAP (V9 and Beyond)

### Planned for V9

1. **Implement align_to_troughs functionality**
   - Modify bandpass algorithms to support phase inversion
   - Wire up checkbox to actual algorithm parameter

2. **Add Bartels Algorithm Option**
   - Implement Bartels cycle detection method
   - Add dropdown menu to select algorithm:
     - Morlet Wavelet (current)
     - Bartels (new)
   - Preserve all existing functionality

3. **Algorithm Comparison Mode**
   - Side-by-side comparison of Morlet vs Bartels
   - Difference heatmap
   - Agreement/disagreement metrics

### Future Enhancements

- Real-time data feeds (Yahoo Finance API)
- Database storage (PostgreSQL) for price data
- User accounts and saved configurations
- Automated cycle trading backtests
- Email/SMS alerts for cycle turning points
- Mobile app (React Native)

---

## SUPPORT & REFERENCES

### Documentation Files

- `README.md` - Quick start guide
- `V8_COMPLETE_DOCUMENTATION.md` - This file (comprehensive reference)
- `FINAL_CONFIGURATION.md` - Configuration notes
- `PRD_CYCLES_DETECTOR_V7.md` - V7 product requirements
- `algorithms/bandpass/BANDPASS_COMPLETE_DOCUMENTATION.md` - Bandpass algorithm details
- `algorithms/scanner_clean/SCANNER_CLEAN_COMPLETE_DOCUMENTATION.md` - Historical scanner

### Key Code Locations

- **Main Application:** `app.py`
- **Frontend:** `templates/index.html`
- **Scanning Algorithm:** `algorithms/heatmap/heatmap_algo.py:80-144`
- **Wavelet Creation:** `algorithms/heatmap/heatmap_algo.py:13-29`
- **Bandpass Generation:** `algorithms/bandpass/wavelet_bandpass.py`
- **Cycle Rating:** `algorithms/cycle_rating.py`
- **Component Yield:** `algorithms/component_yield.py`

### Contact

For questions or issues, refer to project documentation or create detailed reports including:
- V8 version
- Symbol analyzed
- Parameters used
- Expected vs actual behavior
- Screenshots if applicable

---

**END OF V8 COMPLETE DOCUMENTATION**
