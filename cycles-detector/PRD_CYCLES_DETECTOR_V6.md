# Product Requirements Document: Cycles Detector V6

## 1. DATA LAYER

### 1.1 Data Source
- **Provider**: Yahoo Finance via `yfinance` library
- **Data Type**: Daily OHLCV (Open, High, Low, Close, Volume)
- **Used Fields**: Close price only
- **Symbols**: Any valid Yahoo Finance ticker (stocks, ETFs, indices)

### 1.2 Data Manager (`data_manager.py`)

#### Purpose
Automated data acquisition and maintenance system that ensures fresh, accurate historical price data for any symbol.

#### Class: `DataManager`

**Initialization**:
```python
DataManager(symbol='TLT', data_dir='.')
```

**Parameters**:
- `symbol`: Stock ticker (default: 'TLT')
- `data_dir`: Storage directory for CSV files (default: current directory)

**Output Files**:
- `{symbol}_history.csv`: Full historical data (Date, Close)
- `{symbol}_prices.txt`: Price array for backward compatibility

#### Data Flow

**First Time (No existing data)**:
1. Check if `{symbol}_history.csv` exists
2. If not found → Download full history using `yf.Ticker(symbol).history(period='max')`
3. Extract Date and Close columns
4. Convert dates to `datetime.date` objects (NOT Timestamps)
5. Save to CSV
6. Return price array

**Subsequent Runs (Data exists)**:
1. Load existing CSV
2. Check last date in file
3. Compare with today's date
4. If data is older than 1 day:
   - Download new bars from `last_date + 1 day` to today
   - **CRITICAL**: Convert both old and new dates to `datetime.date` format
   - Merge data, remove duplicates, sort by date
   - Save updated CSV
5. Return price array

#### Data Format

**CSV Structure**:
```
Date,Close
2010-06-29,23.45
2010-06-30,23.67
...
```

**Returned Data**:
- `prices`: numpy array of close prices
- `df`: pandas DataFrame with Date and Close columns

#### Key Implementation Details

**Date Handling** (CRITICAL):
```python
# Always ensure date objects, not Timestamps
df['Date'] = pd.to_datetime(df['Date']).dt.date
```

This prevents pandas type mismatch errors when comparing/sorting mixed date types.

**Data Validation**:
- Checks for file existence
- Handles market closure (no new data on weekends)
- Deduplicates on Date column
- Maintains chronological order

### 1.3 Data Requirements by Symbol

**Minimum Data Requirements**:
- Total bars needed: `window_size + (260 weeks × 5 bars/week)`
- For 4000-bar window: Need at least **5,300 bars minimum**
- For shorter histories: System auto-adjusts window size

**Auto-Adjustment Logic**:
```python
max_allowed_window = len(prices) - 1300  # Leave 260 weeks for heatmap
window_size = min(requested_window, max_allowed_window)

if window_size < 500:
    return error  # Insufficient data
```

**Examples**:
- TLT: ~8,000 bars → Uses full 4000-bar window
- TSLA: ~3,840 bars → Auto-adjusts to 2540-bar window
- New IPO with 1000 bars → Returns "Insufficient data" error

### 1.4 Data Storage

**Location**: Same directory as application
**Naming Convention**: `{symbol.lower()}_history.csv`
**Persistence**: Data persists across sessions
**Updates**: Automatic on each request if data is stale

### 1.5 Data Access Pattern

**Per-Request Flow**:
```
1. API receives symbol parameter (e.g., "TSLA")
2. Create SigmaLAnalyzer(symbol)
3. SigmaLAnalyzer.__init__ calls self.load_data()
4. load_data() creates DataManager(symbol)
5. DataManager.get_data() returns (prices, df)
6. Prices stored in self.prices for analysis
```

**No Global State**: Each request gets fresh DataManager instance
**Thread Safety**: No shared state between requests
**Caching**: File-based (CSV files persist, no in-memory cache)

### 1.6 Error Handling

**Data Download Failures**:
- Invalid symbol → yfinance raises exception → caught in app.py
- Network error → yfinance timeout → returns error to user
- No data available → Empty array → "No price data available" error

**File System Errors**:
- Permission denied → Exception raised
- Disk full → Exception raised
- Corrupt CSV → pandas read error → Re-download full history

### 1.7 Data Quality Checks

**Automated Checks**:
- ✓ Date continuity (sorted chronologically)
- ✓ Duplicate removal
- ✓ Type consistency (all dates are date objects)

**Missing Checks** (Future Enhancement):
- Price validity (no negative prices)
- Volume consistency
- Split/dividend adjustments verification

---

## 2. ANALYSIS ENGINE

### 2.1 Core Components

The analysis engine consists of three main algorithmic modules:

1. **Power Spectrum** (`heatmap_algo.py::compute_power`)
2. **Heatmap Generator** (`heatmap_algo.py::process_week_on_grid`)
3. **Bandpass Filter** (`sigma_l_bandpass_filter.py`)

### 2.2 Wavelength Configuration

**Trading Days Grid**:
- Range: 100 to 800 trading days
- Step: 5 trading days (configurable via API)
- Count: 141 wavelengths (default)

**Calendar Days Conversion**:
```python
calendar_days = trading_days × 1.451
# Assumes 252 trading days per year
# 365 / 252 = 1.448 ≈ 1.451
```

**Wavelength Examples**:
| Trading Days | Calendar Days | Period |
|-------------|---------------|--------|
| 100 | 145 | ~5 months |
| 260 | 377 | ~1 year |
| 520 | 754 | ~2 years |
| 800 | 1161 | ~3.2 years |

### 2.3 Window Size Management

**Default**: 4000 bars (~15.8 years)
**Adaptive Logic**:
```python
# Reserve 1300 bars for heatmap history (260 weeks × 5)
max_allowed = total_bars - 1300
actual_window = min(requested_window, max_allowed)
```

**Purpose**: Ensures consistent analysis depth while maintaining sufficient historical context for heatmap

---

## 3. MORLET WAVELET ALGORITHM

### 3.1 High-Q Morlet Wavelet

**Formula**:
```python
Q = 15.0 + 50.0 × frequency
sigma = Q / (2π × frequency)

wavelet = exp(-t²/(2σ²)) × exp(i×2π×freq×t)
```

**Properties**:
- Variable Q-factor (higher Q for lower frequencies)
- Time-domain centered at t=0
- Unit energy normalization

**Implementation** (`heatmap_algo.py:13-26`):
```python
def create_high_q_morlet(freq, length):
    Q = 15.0 + 50.0 * freq
    sigma = Q / (2.0 * np.pi * freq)

    t = np.arange(length) - length/2.0
    envelope = np.exp(-t**2 / (2.0 * sigma**2))
    carrier = np.exp(1j * 2.0 * np.pi * freq * t)
    wavelet = envelope * carrier

    # Normalize to unit energy
    norm = np.sqrt(np.sum(np.abs(wavelet)**2))
    wavelet /= norm

    return wavelet
```

### 3.2 Power Computation

**Process** (`heatmap_algo.py:28-54`):

1. **Wavelet Length Calculation**:
```python
freq = 1.0 / wavelength
cycles = min(8, max(4, n // wavelength))
wavelet_length = min(n, wavelength × cycles)
```

2. **Sliding Window Convolution**:
```python
step = max(1, wavelength // 8)
for center in range(wlen//2, n - wlen//2 + 1, step):
    segment = data[center - wlen//2 : center + wlen//2]
    conv = sum(segment × conj(wavelet))
    power += |conv|²
```

3. **Average Power**:
```python
return sqrt(total_power / count)
```

**Output**: Single scalar power value for given wavelength

---

## 4. POWER SPECTRUM

### 4.1 Purpose
Identifies currently active cycles by measuring wavelet power across all wavelengths for the most recent data. Displays as a bar chart showing cycle strength at each wavelength.

### 4.2 Processing Pipeline

**Input**: Price array, wavelengths, window_size

**Algorithm** (`heatmap_algo.py::process_week_on_grid`):

1. **Data Window Selection**:
   ```python
   rollback = week * 5  # week=0 for current data
   end_idx = len(prices) - rollback
   start_idx = end_idx - window_size
   data = np.log(prices[start_idx:end_idx])
   ```

2. **High-Pass Filter** (if `suppress_long_cycles=True`):
   ```python
   ma_period = min(600, len(data) // 3)
   long_ma = moving_average(data, ma_period)
   data = data - long_ma  # Remove long-term trend
   ```

3. **Linear Detrend**:
   ```python
   x = np.arange(len(data))
   coeffs = np.polyfit(x, data, 1)
   trend = np.polyval(coeffs, x)
   data = data - trend
   ```

4. **Compute Power** (for each wavelength):
   - Call `compute_power(data, wavelength)` (see Section 3.2)
   - Returns scalar power value

5. **Scanner Processing** (see Section 4.3)

6. **Global Normalization**:
   ```python
   # Normalize AFTER collecting all heatmap data
   power_spectrum = power_spectrum_raw / global_max
   ```

**Output**: Array of globally normalized power values [0, 1]

### 4.2.1 Implementation Location
- **File**: `algorithms/heatmap/heatmap_algo.py`
- **Function**: `process_week_on_grid(prices, week, wavelengths, window_size, suppress_long_cycles, normalize)`
- **Called by**: `app.py::analyze()` line 82

### 4.3 Scanner Processing

**Median Filter** (noise reduction):
```python
for i in range(n):
    filtered[i] = median(spectrum[i-1:i+2])
```

**Smoothing** (5-point moving average):
```python
smoothed = convolve(filtered, ones(5)/5)
```

**Peak Enhancement**:
```python
mean_val = mean(smoothed)
enhanced[smoothed > mean] = mean + 2×(smoothed - mean)
```

### 4.4 Peak Detection

**Criteria**:
- Minimum height: 0.25 (normalized)
- Minimum distance: 8 wavelengths
- Maximum peaks: Top 6

**Output Format**:
```json
{
  "wavelength": 682,
  "amplitude": 0.89,
  "period_years": 1.87
}
```

---

## 5. CYCLE HEATMAP

### 5.1 Purpose
Interactive time-frequency heatmap showing how cycle strength evolved over historical window. Enables visual identification of:
- Persistent cycles (bright horizontal bands across time)
- Emerging cycles (bands that strengthen toward left/current)
- Fading cycles (bands that weaken toward left/current)

### 5.2 Data Structure

**Backend Format**: `[weeks × wavelengths]`
- Weeks: Up to 366 (calculated as `(len(prices) - window_size) // 5`)
- Wavelengths: 141 (100-800 calendar days, step=5)
- Total cells: ~51,600 values

**Time Indexing** (Backend):
```python
week_0 = most_recent (NOW)
week_365 = ~7_years_ago

rollback_bars = week × 5  # Each week = 5 trading days
end_idx = len(prices) - rollback
start_idx = end_idx - window_size
```

**Frontend Transformation** (`index.html:729-731`):
```javascript
// Backend sends [week][wavelength]
// Transpose to [wavelength][week] for Plotly
// REVERSE time axis so current data appears on LEFT
const heatmapFlipped = data.heatmap.wavelengths.map((_, wlIndex) =>
    data.heatmap.data.map(weekData => weekData[wlIndex]).reverse()
);
```

**Displayed Orientation**:
- **X-axis (Time)**: LEFT = current, RIGHT = historical
- **Y-axis (Wavelength)**: BOTTOM = 100d, TOP = 800d
- **Color**: BLACK = weak (0.0), PURPLE = medium (0.5), WHITE = strong (1.0)

### 5.3 Global Normalization

**CRITICAL**: Heatmap and power spectrum MUST use same normalization scale.

**Algorithm**:
```python
# Collect ALL spectra unnormalized
all_spectra = []
for week in range(260):
    spectrum = compute_spectrum(week, normalize=False)
    all_spectra.append(spectrum)

# Find global maximum
global_max = max(all_spectra)

# Normalize ALL data (including power spectrum)
heatmap = all_spectra / global_max
power_spectrum = current_spectrum / global_max
```

**Why Global Normalization?**:
- Ensures visual consistency between heatmap and power spectrum
- Bright in power spectrum → Bright in heatmap (if cycle was strong historically)
- Dim in power spectrum → Dim in heatmap
- Reveals newly emerging vs. historically strong cycles

### 5.4 Historical Window Alignment

**Fixed Window Size**: Uses SAME window_size as power spectrum
```python
for week in range(260):
    rollback = week × 5
    end_idx = total_bars - rollback
    start_idx = end_idx - window_size
    data = prices[start_idx:end_idx]
    # Compute spectrum...
```

**Why Fixed Window?**:
- Prevents bias from varying window lengths
- Maintains consistent frequency resolution across time
- Enables accurate comparison of cycle strength over time

### 5.5 High-Pass Filtering (Optional)

**Purpose**: Suppress ultra-long cycles (>600 trading days = ~870 calendar days)

**Method**:
```python
ma_period = min(600, len(data) // 3)
long_ma = moving_average(data, ma_period)
filtered_data = data - long_ma
```

**Trade-off**:
- ✓ Reduces dominance of multi-year trends
- ✗ May partially suppress 625d-800d cycles near cutoff

### 5.6 Visualization Implementation

**Colorscale** (`index.html:737-745`):
```javascript
colorscale: [
    [0,    '#000000'],  // Black (no cycle)
    [0.15, '#1a0033'],  // Deep purple
    [0.30, '#330066'],  // Dark purple
    [0.50, '#6600cc'],  // Medium purple
    [0.70, '#9933ff'],  // Bright purple
    [0.85, '#cc66ff'],  // Light purple
    [1,    '#ffffff']   // White (strong cycle)
]
```

**Cycle Labels** (`index.html:773-810`):
- Positioned on RIGHT margin
- Yellow triangles (◄) pointing LEFT to current bright bands
- Labels show wavelength in calendar days (e.g., "625")
- Only displayed for peaks with amplitude ≥ 0.15

**X-Axis Range** (`index.html:840`):
```javascript
range: [0, totalWeeks + 3]  // Extends to include label area
```

**Time Labels**:
- Automatic year markers (2018, 2019, 2020, etc.)
- Calculated based on `totalWeeks * 5 trading days / 252 days/year`

---

## 6. API SPECIFICATION

### 6.1 Endpoint

```
GET /api/analyze
```

### 6.2 Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | string | 'TLT' | Yahoo Finance ticker |
| `window_size` | int | 4000 | Analysis window (bars) |
| `min_wavelength` | int | 100 | Min wavelength (trading days) |
| `max_wavelength` | int | 800 | Max wavelength (trading days) |
| `wavelength_step` | int | 5 | Grid resolution |
| `phase_method` | string | 'hilbert' | Phase calculation method |
| `phase_window_size` | int | 1000 | Phase analysis window |
| `suppress_long_cycles` | bool | true | Apply high-pass filter |
| `heatmap_years` | int | 10 | Years of heatmap history |

### 6.3 Response Format

```json
{
  "symbol": "TLT",
  "peak_cycles": [
    {
      "wavelength": 682,
      "amplitude": 0.89,
      "period_years": 1.87
    }
  ],
  "power_spectrum": {
    "wavelengths": [145, 152, ...],
    "values": [0.23, 0.45, ...]
  },
  "heatmap": {
    "data": [[...], [...], ...],
    "weeks": 260
  },
  "bandpass": {
    "wavelength": 682,
    "values": [...],
    "peaks": [...],
    "troughs": [...]
  }
}
```

### 6.4 Error Responses

```json
{
  "error": "No price data available"
}
```

```json
{
  "error": "Insufficient data for XXXX. Need at least 1800 bars, have 1000"
}
```

---

## 7. BANDPASS FILTER

### 7.1 Purpose
Isolate and visualize a specific cycle wavelength for precise timing of entry/exit points. Shows the isolated cycle oscillation as a clean sine-like wave.

### 7.2 Pure Sine Wave Implementation

**Current Method** (`sigma_l_bandpass_filter.py:4-21`):
```python
def create_bandpass_filter(length, wavelength, phase=0):
    """
    Generate pure sine wave bandpass for given wavelength

    Args:
        length: Total length (historical + future)
        wavelength: Cycle period in trading days
        phase: Phase offset in radians

    Returns:
        numpy array of sine values
    """
    t = np.arange(length)
    frequency = 1.0 / wavelength
    bandpass = np.sin(2 * np.pi * frequency * t + phase)
    return bandpass
```

**Why Pure Sine?**:
- Clean, interpretable visualization
- No lag (compared to MA-based methods)
- Perfect for phase-aligned projection
- Matches SIGMA-L's visual style

### 7.3 Phase Optimization

**Critical**: The phase determines where peaks/troughs align with actual price action.

**Peak Matching Algorithm** (`app.py:257-355`):

1. **Detrend Price Data**:
   ```python
   x = np.arange(window_size)
   coeffs = np.polyfit(x, prices_subset, 4)  # 4th degree polynomial
   trend = np.polyval(coeffs, x)
   detrended = prices_subset - trend
   ```

2. **Find Actual Price Peaks**:
   ```python
   min_peak_distance = int(wavelength * 0.6)
   price_peaks, _ = find_peaks(detrended,
                               distance=min_peak_distance,
                               prominence=std(detrended) * 0.3)
   ```

3. **Calculate Phase from Last Peak**:
   ```python
   last_peak_idx = recent_peaks[-1]

   # Want: sin(2π * peak_idx / wavelength + phase) = 1 (peak)
   # So: 2π * peak_idx / wavelength + phase = π/2
   # Therefore: phase = π/2 - 2π * peak_idx / wavelength

   phase = (π/2) - (2π * last_peak_idx / wavelength)
   phase = phase % (2π)  # Normalize to [0, 2π]
   ```

4. **Validate Alignment**:
   ```python
   test_sine = sin(2π * arange(window_size) / wavelength + phase)
   test_peaks = find_peaks(test_sine)

   # Check alignment error for recent price peaks
   for price_peak in recent_peaks:
       distances = [abs(price_peak - sine_peak) for sine_peak in test_peaks]
       alignment_error = min(distances)

   # If error > 15% of wavelength, fine-tune phase
   if mean(alignment_errors) > wavelength * 0.15:
       # Try 30 phase adjustments ±π/6
       # Select phase with minimum alignment error
   ```

**Output**: Optimal phase in radians for perfect peak alignment

### 7.4 Future Projection

**Extended Timeline**:
```python
future_days = int(selected_wavelength * 2)  # Project 2 full cycles ahead
total_length = len(prices) + future_days
bandpass = create_bandpass_filter(total_length, selected_wavelength, optimal_phase)
```

**Visual Separation**:
- Historical portion: Solid line
- Future projection: Dashed line
- Transition point: Current date

### 7.5 Peak/Trough Detection

**Algorithm** (`sigma_l_bandpass_filter.py:23-47`):
```python
def find_peaks_and_troughs(bandpass):
    # Find peaks: local maxima
    peaks, _ = find_peaks(bandpass)

    # Find troughs: local minima (peaks of inverted signal)
    troughs, _ = find_peaks(-bandpass)

    return peaks, troughs
```

**Visual Markers**:
- **Peaks**: Red circles at local maxima
- **Troughs**: Green circles at local minima
- **Labels**: Date labels ("7 Aug 2025") in vertical text

**Trading Interpretation**:
- Peak approaching → Consider reducing long positions
- At peak → Potential sell/short entry
- Trough approaching → Consider reducing short positions
- At trough → Potential buy/long entry

### 7.6 Scaling for Price Overlay

**Purpose**: Display bandpass wave overlaid on actual price chart

**Algorithm** (`app.py:166-169`):
```python
price_mean = np.mean(prices)
price_range = np.max(prices) - np.min(prices)
scaled_bandpass = bandpass * (price_range * 0.10) + price_mean
```

**Scaling Factor**: 10% of price range
- Makes oscillation visible without dominating chart
- Centers around mean price
- Preserves phase and frequency

### 7.7 Alternative Phase Methods

**Correlation Method** (`app.py:421-479`):

1. **Test All Phases** (720 steps = 0.5° resolution):
   ```python
   for i in range(720):
       phase = 2π * i / 720
       sine_wave = sin(2π * t / wavelength + phase)
       corr = corrcoef(detrended_price, sine_wave)[0,1]
   ```

2. **Add Peak Alignment Bonus**:
   ```python
   # If sine peaks align with price peaks within 10% of wavelength
   alignment_bonus = 0.05 per aligned peak
   total_score = abs(corr) + alignment_bonus
   ```

3. **Select Best**:
   ```python
   optimal_phase = phase with max(total_score)
   ```

**Trade-off**:
- ✓ More interpretable (correlation value)
- ✓ Explicit alignment checking
- ✗ Slower (720 iterations vs. direct calculation)
- ✗ May miss subtle phase shifts

---

## 8. FRONTEND

### 8.1 Technology Stack
- **Framework**: Vanilla JavaScript (no framework)
- **Charts**: Plotly.js
- **Styling**: Dark theme, purple accent

### 8.2 UI Components

**Layout**:
```
+----------------------------------+
|  Symbol Input | Window Size      |
+----------------------------------+
|                                  |
|     Power Spectrum Chart         |
|                                  |
+----------------------------------+
|                                  |
|         Heatmap Chart            |
|                                  |
+----------------------------------+
|                                  |
|       Bandpass Filter            |
|                                  |
+----------------------------------+
```

### 8.3 Interactions

**Symbol Change**:
1. User enters ticker
2. Auto-uppercase
3. API call with new symbol
4. All charts update

**Wavelength Selection**:
1. Click bar in power spectrum
2. Update bandpass to selected cycle
3. Show phase info
4. Highlight in heatmap (future)

**Real-time Updates**:
- Data refreshes on page load
- Manual refresh button
- Shows data freshness indicator

---

## 9. DEPLOYMENT

### 9.1 Development Server
```bash
cd webapp
python3 app.py
```

Access: http://localhost:5001

### 9.2 File Structure
```
webapp/
├── app.py                    # Flask backend
├── data_manager.py           # Data acquisition
├── algorithms/
│   ├── heatmap/
│   │   └── heatmap_algo.py  # Power spectrum + heatmap
│   └── bandpass/
│       └── sigma_l_bandpass_filter.py
├── templates/
│   └── index.html           # Frontend
└── {symbol}_history.csv     # Data cache
```

### 9.3 Dependencies
```
Flask
numpy
pandas
scipy
yfinance
```

---

## 10. KNOWN ISSUES & LIMITATIONS

### 10.1 Current Limitations

**Data**:
- Only daily data (no intraday)
- Requires minimum 1800 bars
- No handling of stock splits/dividends validation

**Analysis**:
- High-pass filter may suppress 625d-800d cycles
- No confidence intervals on cycle detection
- Peak detection threshold (0.25) is fixed

**UI**:
- No mobile optimization
- No chart export functionality
- No historical comparison tool

### 10.2 Future Enhancements

**Priority 1**:
- [ ] Add confidence bands to power spectrum
- [ ] Optimize heatmap rendering speed
- [ ] Add multi-symbol comparison

**Priority 2**:
- [ ] Intraday data support
- [ ] Export to CSV/Excel
- [ ] Saved analysis sessions

**Priority 3**:
- [ ] Machine learning cycle prediction
- [ ] Alert system for cycle peaks/troughs
- [ ] Mobile app

---

## 11. VALIDATION & TESTING

### 11.1 Test Cases

**Data Layer**:
- ✓ Fresh symbol download (TLT)
- ✓ Incremental update (existing data)
- ✓ Type mismatch fix (date objects)
- ✓ Insufficient data handling (TSLA auto-adjust)

**Analysis**:
- ✓ Global normalization (625d consistency)
- ✓ Window size adaptation (TSLA 3840 bars)
- ✓ Peak detection (top 6, threshold 0.25)

**API**:
- ✓ Multi-symbol support
- ✓ Parameter validation
- ✓ Error handling

### 11.2 Performance Benchmarks

**Data Download**:
- First time (5000 bars): ~2-3 seconds
- Update (1-5 bars): ~0.5 seconds

**Analysis**:
- Power spectrum (141 wavelengths): ~1 second
- Heatmap (260 weeks × 141 wavelengths): ~30 seconds
- Bandpass filter: ~0.1 seconds

**Total Request Time**: 30-35 seconds (dominated by heatmap)

---

## 12. MAINTENANCE

### 12.1 Data Cleanup
```bash
# Remove all cached data
rm *_history.csv *_prices.txt
```

### 12.2 Troubleshooting

**"No price data available"**:
- Check symbol validity
- Verify yfinance connection
- Check date type consistency in CSV

**Slow performance**:
- Reduce wavelength_step (fewer wavelengths)
- Reduce heatmap_years
- Consider caching results

**Visualization issues**:
- Check global normalization
- Verify wavelength alignment
- Inspect data for NaN/Inf values

---

## APPENDIX A: Key Algorithms

### A.1 Global Normalization Implementation
```python
# In app.py::analyze()
# Step 1: Collect raw spectra
power_spectrum_raw = process_week_on_grid(..., normalize=False)
heatmap_raw = []
for week in range(max_weeks):
    spectrum = process_week_on_grid(week, ..., normalize=False)
    heatmap_raw.append(spectrum)

# Step 2: Find global max
heatmap_raw = np.array(heatmap_raw)
global_max = np.max(heatmap_raw)

# Step 3: Normalize all together
if global_max > 0:
    heatmap_data = (heatmap_raw / global_max).tolist()
    power_spectrum = power_spectrum_raw / global_max
```

### A.2 Window Size Auto-Adjustment
```python
# In app.py::analyze()
max_allowed_window = len(self.prices) - 1300
if window_size is None:
    window_size = min(4000, max_allowed_window)
else:
    window_size = min(window_size, max_allowed_window)

if window_size < 500:
    return {"error": f"Insufficient data..."}
```

### A.3 Date Type Fix
```python
# In data_manager.py::_update_if_needed()
new_data['Date'] = pd.to_datetime(new_data['Date']).dt.date
df['Date'] = pd.to_datetime(df['Date']).dt.date  # CRITICAL: Convert existing data too
```

---

## APPENDIX B: Complete File Specifications

### B.1 Core Algorithm Files

**`algorithms/heatmap/heatmap_algo.py`** (143 lines):
- `create_high_q_morlet(freq, length)` (lines 13-26): Morlet wavelet generation
- `compute_power(data, wavelength)` (lines 28-54): Power calculation via convolution
- `process_week_on_grid(prices, week, wavelengths, ...)` (lines 56-143): Main spectrum computation
  - Data window extraction
  - High-pass filtering (optional)
  - Linear detrending
  - Per-wavelength power calculation
  - Scanner processing (median + smoothing + enhancement)

**`algorithms/bandpass/sigma_l_bandpass_filter.py`** (47 lines):
- `create_bandpass_filter(length, wavelength, phase)` (lines 4-21): Pure sine wave generation
- `find_peaks_and_troughs(bandpass)` (lines 23-47): Peak/trough detection

**`data_manager.py`** (112 lines):
- `DataManager.__init__(symbol, data_dir)` (lines 13-17): Initialization
- `get_data()` (lines 19-43): Main entry point
- `_download_full_history()` (lines 45-57): Initial download
- `_update_if_needed()` (lines 59-98): Incremental updates with timezone handling

### B.2 Backend Server

**`app.py`** (639 lines):

**Class: SigmaLAnalyzer** (lines 31-479):
- `__init__(symbol)` (lines 32-36): Constructor with data loading
- `load_data()` (lines 38-46): DataManager integration
- `analyze(...)` (lines 48-206): Main analysis pipeline
  - Window size auto-adjustment (lines 62-76)
  - Power spectrum computation (lines 82-84)
  - Heatmap generation (lines 87-106)
  - Global normalization (lines 98-106)
  - Peak detection (lines 108-122)
  - Bandpass generation (lines 125-156)
  - Response formatting (lines 171-206)
- `find_optimal_phase_peak_matching(...)` (lines 257-355): Primary phase algorithm
- `find_optimal_phase_correlation(...)` (lines 421-479): Alternative phase method

**Flask Routes**:
- `/` (lines 482-485): Serve index.html
- `/api/analyze` (lines 487-524): Main analysis endpoint
- `/api/bandpass` (lines 526-601): Generate bandpass for specific cycle
- `/api/config` (lines 603-615): Configuration info

**Server Configuration** (lines 617-639):
- Port: 5001
- Debug mode: True
- Cache headers: Disabled

### B.3 Frontend

**`templates/index.html`** (1521 lines):

**Structure**:
- HTML/CSS (lines 1-350): Layout, styling, controls
- JavaScript (lines 351-1521): Application logic

**Key JavaScript Functions**:
- `runAnalysis()` (lines 388-462): API call and orchestration
- `updatePowerSpectrum(data)` (lines 465-527): Power spectrum chart
- `updateBandpassUnscaled(data)` (lines 530-651): Bandpass oscillator chart
- `updateCyclesList(cycles)` (lines 653-727): Detected cycles list
- `updateHeatmap(data)` (lines 729-899): Heatmap visualization
  - Time reversal (line 731): `data.map(...).reverse()`
  - Colorscale (lines 737-745): Black to purple to white
  - Cycle annotations (lines 773-810): Right-side labels
  - X-axis range (line 840): `[0, totalWeeks + 3]`
- `loadNewCycle(wavelength)` (lines 1075-1155): Dynamic bandpass loading
- `updateBandpassChart(data)` (lines 1321-1517): Detailed bandpass with zoom

**Chart Configurations**:
- Power Spectrum: Vertical bar chart, purple bars
- Heatmap: Reversed time axis (LEFT=now, RIGHT=past)
- Bandpass: Dual-trace (historical solid, future dashed)

### B.4 Data Files (Generated)

**Format**: `{symbol.lower()}_history.csv`
```csv
Date,Close
2010-06-29,23.45
2010-06-30,23.67
```

**Storage**: Same directory as app.py
**Lifecycle**: Persists across sessions, auto-updates when stale

### B.5 Configuration Constants

**Wavelength Grid** (app.py:79):
```python
wavelengths = np.arange(100, 801, 1)  # Trading days
```

**Window Size** (app.py:69):
```python
default_window = 4000  # ~15.8 years
```

**Peak Detection** (app.py:109):
```python
find_peaks(power_spectrum, height=0.25, distance=8)
```

**High-Pass Filter** (heatmap_algo.py:89-92):
```python
ma_period = min(600, len(data) // 3)
```

**Phase Window** (app.py:133):
```python
phase_window_size = 1000  # bars for phase calculation
```

**Future Projection** (app.py:144):
```python
future_days = int(selected_wavelength * 2)
```

### B.6 Critical Bug Fixes Applied

**Date Type Consistency** (data_manager.py:53, 78, 81):
```python
df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None).dt.date
```
Prevents pandas type mismatch when merging/comparing dates.

**Heatmap Time Reversal** (index.html:731):
```javascript
.map(weekData => weekData[wlIndex]).reverse()
```
Displays current data on LEFT (was showing on RIGHT).

**Cache Busting** (index.html:6-8):
```html
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```
Prevents browser from caching old JavaScript code.

---

## APPENDIX C: API Call Examples

### C.1 Basic Analysis
```bash
curl "http://localhost:5001/api/analyze?symbol=TLT"
```

### C.2 With Parameters
```bash
curl "http://localhost:5001/api/analyze?\
symbol=AAPL&\
window_size=3000&\
min_wavelength=100&\
max_wavelength=600&\
suppress_long_cycles=true"
```

### C.3 Futures Symbol
```bash
curl "http://localhost:5001/api/analyze?symbol=CL%3DF"
# Note: %3D is URL-encoded '='
```

### C.4 Custom Bandpass
```bash
curl "http://localhost:5001/api/bandpass?\
symbol=TLT&\
selected_wavelength=625&\
phase_method=hilbert"
```

---

## APPENDIX D: Version History

**V6.0** (2025-10-03):
- Fixed heatmap time axis orientation (reversed display)
- Added cache-busting meta tags
- Removed "Trading Days" from Y-axis label
- Extended X-axis range to include annotations
- Fixed date type consistency for futures symbols (CL=F)
- Documented complete system in PRD

**V5.0** (Prior):
- Global normalization between power spectrum and heatmap
- Peak-based phase matching algorithm
- Pure sine wave bandpass (replaced MA-based method)

**V4.0** (Prior):
- Multi-symbol support via Yahoo Finance
- DataManager with auto-update
- Adaptive window sizing

---

*Document Version: 2.0 - LOCKED*
*Last Updated: 2025-10-03*
*System: Cycles Detector V6*
*Status: PRODUCTION - DO NOT MODIFY V6*
