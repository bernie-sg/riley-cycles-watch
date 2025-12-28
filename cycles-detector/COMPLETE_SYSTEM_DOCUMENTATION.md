# Complete Cycles Detector System Documentation

## Overview

This application detects market cycles using multiple detection algorithms and provides comprehensive quality metrics to help traders identify the most reliable trading signals.

---

## 🔬 Cycle Detection Algorithms

The system supports three detection methods, selectable via the "Scan Algorithm" dropdown:

### 1. Morlet Wavelet Transform (CWT) [Default]

**What it does**: Decomposes price data into its frequency components to find dominant cycles.

**Algorithm**:
```
For each wavelength (100-800 days):
  1. Create Morlet wavelet with Q=50 (high selectivity)
  2. Convolve wavelet with price data at multiple time windows
  3. Calculate RMS power = sqrt(mean(|convolution|²))
  4. Average power across sliding windows
```

**Key Parameters**:
- **Q = 50**: High sharpness for precise frequency detection
- **Uniform Q**: All wavelengths detected with equal sensitivity (no bias)
- **Sliding Windows**: Multiple windows averaged for stability

**Output**: Power spectrum showing strength of each cycle frequency

**Best for**: Clean, consistent data with clear cyclical patterns

---

### 2. Goertzel Algorithm [NEW - V12]

**What it does**: Efficiently detects specific frequencies using a targeted detection algorithm, particularly effective in noisy/choppy markets.

**Algorithm**:
```
For each wavelength (100-800 days):
  1. Convert wavelength to frequency (f = 1/wavelength)
  2. Apply Goertzel algorithm to detect magnitude at that frequency
  3. Build power spectrum from detected magnitudes
  4. Normalize and smooth spectrum
```

**Key Advantages**:
- **More robust to noise**: Better at isolating cycles in choppy/volatile markets
- **Computationally efficient**: Faster than full wavelet transform for targeted frequencies
- **Precise frequency detection**: Excellent at finding specific cycles in noisy data

**When to use**:
- Market is very choppy/volatile
- Morlet wavelet produces weak or unclear signals
- Need to detect cycles in high-noise environments
- Short-term trading in erratic markets

**Output**: Power spectrum with cycles detected despite noise

**Best for**: Noisy, volatile, or choppy market conditions

---

### 3. MESA (Maximum Entropy Spectrum Analysis)

**What it does**: Uses maximum entropy method to detect dominant cycles with high statistical confidence.

**Key Features**:
- Extrapolates frequency spectrum using autoregressive modeling
- Provides statistical significance scores
- Good for detecting dominant cycles

**Best for**: Statistical validation of cycle presence

---

## 📋 Algorithm Comparison

| Algorithm | Best For | Noise Handling | Speed | Typical Use Case |
|-----------|----------|----------------|-------|------------------|
| **Morlet** | Clean data | Moderate | Fast | Default analysis, clear trends |
| **Goertzel** | Noisy data | Excellent | Very Fast | Choppy markets, volatile conditions |
| **MESA** | Statistical validation | Good | Slow | Confirming cycle existence |

**Recommendation**: Start with Morlet (default). If results are unclear or market is choppy, switch to Goertzel.

---

## 📊 Power Spectrum & Amplitude

### What is "Amplitude" in the Spectrum?

The amplitude shown in the power spectrum is **NOT price amplitude**. It is:

**RMS Power** = Root Mean Square of the wavelet transform coefficients

**Calculation**:
```python
def compute_power(prices, wavelength):
    # Create Morlet wavelet for this frequency
    freq = 1.0 / wavelength
    wavelet = create_high_q_morlet(freq, wavelength_length)

    # Convolve with price data at multiple windows
    total_power = 0
    for window_center in price_data:
        convolution = convolve(price_window, wavelet)
        power = sqrt(mean(abs(convolution)²))
        total_power += power

    # Average across all windows
    return total_power / num_windows
```

**What it means**:
- **High amplitude** = Strong, consistent cycle at that frequency
- **Low amplitude** = Weak or absent cycle
- Units are **normalized** (0-1 scale after smoothing)
- Peak height indicates **cycle strength**, not price movement size

---

## ⚙️ Letter Rating System (A/B/C/D)

### What It Measures
**Statistical quality** of the cycle signal

### The 5 Metrics

#### 1. **Amplitude Stationarity** (0-100%)
**Measures**: How consistent the wave height is over time

**Calculation**:
```python
# Find all peak-to-trough amplitudes
amplitudes = [abs(peak - trough) for each cycle]

# Calculate coefficient of variation
CV = std(amplitudes) / mean(amplitudes)

# Convert to stationarity (lower CV = higher stationarity)
stationarity = exp(-2 * CV) * 100%
```

**Interpretation**:
- **100%** = Perfectly consistent wave heights
- **80%+** = Highly stationary (A-rating threshold)
- **<60%** = Erratic, unreliable

---

#### 2. **Frequency Stationarity** (0-100%)
**Measures**: How consistent the wavelength is over time

**Calculation**:
```python
# Measure actual wavelengths via zero-crossings
zero_crossings = find_zero_crossings(bandpass)
wavelengths = [distance between crossings for each full cycle]

# Calculate variation
CV = std(wavelengths) / mean(wavelengths)

# Penalize deviation from expected wavelength
error = abs(mean(wavelengths) - expected_wavelength) / expected_wavelength

# Combined score
stationarity = exp(-2 * CV - error) * 100%
```

**Interpretation**:
- **100%** = Rock-solid period (e.g., exactly 360 days every time)
- **80%+** = Very consistent (A-rating threshold)
- **<60%** = Period jumps around randomly

---

#### 3. **Spectral Isolation** (0-100%)
**Measures**: How well-separated this cycle is from other cycles

**Calculation**:
```python
# Find nearest competing cycle
nearest_cycle = find_closest_peak_in_spectrum(exclude_self)

# Calculate wavelength separation
wl_separation = abs(wavelength - nearest_wavelength) / wavelength

# Calculate power dominance
power_ratio = peak_power / nearest_peak_power

# Combined isolation score
isolation = (wl_separation * 0.5 + tanh(power_ratio - 1) * 0.5) * 100%
```

**Interpretation**:
- **100%** = No nearby competing cycles
- **70%+** = Well-isolated (A-rating threshold)
- **<50%** = Crowded, overlapping with others

---

#### 4. **Signal-to-Noise Ratio (SNR)**
**Measures**: How much stronger the cycle is vs background noise

**Calculation**:
```python
# Peak power at cycle frequency
signal = spectrum[peak_wavelength]

# Noise level (regions away from peak)
noise = mean(spectrum[far_from_peak])

# SNR ratio
SNR = signal / noise
```

**Interpretation**:
- **>5.0** = Excellent signal clarity (A-rating threshold)
- **>3.0** = Good clarity (B-rating threshold)
- **<2.0** = Mostly noise

---

#### 5. **Gain Rank**
**Measures**: Where this cycle ranks in power/strength

**Calculation**:
```python
# Rank all peaks by power
sorted_peaks = sort_descending(spectrum)

if cycle_power >= sorted_peaks[0] * 0.95:
    rank = 1  # Strongest cycle
elif cycle_power >= sorted_peaks[1] * 0.95:
    rank = 2  # Second strongest
else:
    rank = 3+  # Weaker cycles
```

**Interpretation**:
- **Rank 1** = Dominant cycle (required for A-rating)
- **Rank 1-2** = Strong cycles (B-rating threshold)
- **Rank 3+** = Secondary cycles

---

### Rating Classification Logic

```python
if (amp_stat > 80% and freq_stat > 80% and
    gain_rank == 1 and isolation > 70% and SNR > 5.0):
    rating = 'A' (🔥)  # WOW signal - beacon-like

elif (amp_stat > 70% and freq_stat > 70% and
      gain_rank <= 2 and isolation > 60% and SNR > 3.0):
    rating = 'B' (👌)  # Excellent - clear & tradeable

elif (amp_stat > 60% and freq_stat > 60% and
      gain_rank <= 2 and SNR > 2.0):
    rating = 'C' (👍)  # Good - use with caution

else:
    rating = 'D' (⚠️)  # Weak - risky to trade
```

---

## 💰 Component Yield Calculation

### What It Is
**Theoretical trading performance** if you perfectly traded the cycle's peaks and troughs.

### Algorithm

**NOT from Sigma-L PDFs** - This is our own trading simulation:

```python
def calculate_component_yield(bandpass, prices, wavelength):
    # 1. Find peaks (sell signals) and troughs (buy signals)
    peaks = find_peaks(bandpass, distance=wavelength//4)
    troughs = find_peaks(-bandpass, distance=wavelength//4)

    # 2. Create chronological event list
    events = []
    for trough in troughs:
        events.append(('buy', index, price[index]))
    for peak in peaks:
        events.append(('sell', index, price[index]))

    events.sort_by_time()

    # 3. Execute trades (long-only)
    cumulative_yield = 0
    position = None

    for action, index, price in events:
        if action == 'buy' and no_position:
            # Enter long at trough
            position = price

        elif action == 'sell' and holding_position:
            # Exit long at peak
            trade_return = (sell_price - buy_price) / buy_price * 100
            cumulative_yield += trade_return
            position = None

    return cumulative_yield
```

### Example
```
Price Data:
  Buy at trough:  $100 (bandpass at minimum)
  Sell at peak:   $110 (bandpass at maximum)
  → Trade return: 10%

  Buy at trough:  $108
  Sell at peak:   $130
  → Trade return: 20.4%

  Cumulative Yield: 10% + 20.4% = 30.4%
```

### Interpretation
- **>100%** = Excellent trading performance (A/B yield rating)
- **50-100%** = Good performance (C yield rating)
- **<50%** = Weak performance (D yield rating)

### Important Notes
⚠️ **This is theoretical "perfect" trading** (hindsight)
⚠️ **Does NOT account for**: slippage, commissions, realistic entry/exit timing
⚠️ **Purpose**: Compare cycle quality, not predict actual returns

---

## ⭐ Star Rating System (V12 - Harmonic Validation)

### What It Measures
**Physical validity** based on Hurst's harmonic theory

### Harmonic Theory (J.M. Hurst)
**Real market cycles are harmonically related** by simple ratios:
- 2:1 ratio (720d → 360d)
- 3:1 ratio (720d → 240d)
- 4:1 ratio (720d → 180d)

**Example Family**:
```
720d (base)
 ├─ 360d (half)
 ├─ 240d (third)
 └─ 180d (quarter)
     └─ 90d (half of 180d)
```

### Detection Algorithm

```python
def find_harmonic_families(cycles, tolerance=0.15):
    # Build adjacency graph
    for cycle_A in cycles:
        for cycle_B in cycles:
            ratio = wavelength_B / wavelength_A

            # Check if ratio matches 2:1, 3:1, 4:1, 0.5:1, etc.
            if ratio matches any harmonic_ratio within ±15%:
                mark_as_harmonically_related(cycle_A, cycle_B)

    # Find connected components (families)
    families = depth_first_search(harmonic_graph)

    # Identify orphans (no harmonic partners)
    orphans = [cycles with no connections]

    return families, orphans
```

### Quality Score (0-100)

**50 points from SNR**:
- SNR ≥ 5.0 → 50 points
- SNR ≥ 3.0 → 40 points
- SNR ≥ 2.0 → 25 points
- SNR < 2.0 → 10 points

**50 points from Harmonic Family**:
- 3+ partners → 50 points (large family)
- 2 partners → 40 points (medium family)
- 1 partner → 25 points (small family)
- 0 partners → 0 points (orphan)

**Total Score → Star Rating**:
- 80-100 → ⭐⭐⭐⭐ (Excellent)
- 60-79 → ⭐⭐⭐ (Good)
- 40-59 → ⭐⭐ (Fair)
- 0-39 → ⭐ (Poor)

### Orphan Cycles
**Definition**: Cycles with **no harmonic partners**

**Why they matter**:
- Likely noise or measurement artifacts
- Not real market rhythms
- Unreliable for trading

**Displayed in red** to warn users

---

## 🎯 Combined Trading Strategy

### Best Signals (High Confidence)
```
Letter: A or B
Stars: ⭐⭐⭐⭐ or ⭐⭐⭐
→ Use for PRIMARY trading signals
```

### Good Signals (Moderate Confidence)
```
Letter: B or C
Stars: ⭐⭐⭐
→ Use for SECONDARY signals or confirmation
```

### Avoid
```
Letter: D (any stars)
Stars: ⭐ (any letter)
→ Don't trade - too unreliable
```

---

## 📈 Workflow Summary

```
1. DETECTION (Morlet CWT)
   ↓
   Power Spectrum → Find peaks (dominant cycles)

2. EXTRACTION (Bandpass Filter)
   ↓
   Isolate each cycle → Create pure sine-like wave

3. QUALITY ANALYSIS
   ↓
   Calculate 5 metrics → Assign A/B/C/D rating

4. YIELD SIMULATION
   ↓
   Trade peaks/troughs → Calculate theoretical return

5. HARMONIC VALIDATION (V12)
   ↓
   Find families → Assign ⭐ rating

6. TRADING DECISION
   ↓
   Combine letter + stars → Choose best signals
```

---

## 🔍 System Architecture

### Core Components
✅ Morlet wavelet analysis for cycle detection
✅ Bandpass filtering for cycle isolation
✅ Stationarity-based quality metrics
✅ High-Q wavelets for precision

### Advanced Features
➕ **Component Yield**: Trading simulation for cycle quality comparison
➕ **Star Ratings**: Hurst harmonic validation
➕ **Comprehensive metrics**: Full A/B/C/D classification system
➕ **Health Metrics**: Amplitude consistency and wavelength stability tracking

### Future Enhancements
⏳ **VTL (Valid Trend Lines)**: Planned for future release
⏳ **Automated FLD Trading**: FLD visualization available, automated signals planned

---

## 💡 Pro Tips

1. **Always check BOTH ratings** - Don't trade on letter rating alone
2. **Prioritize harmonic families** - 4-star cycles more reliable than orphans
3. **A + ⭐⭐⭐⭐ = Gold standard** - Best possible signal
4. **Orphans are suspect** - Even A-rated orphans may be noise
5. **Yield is theoretical** - Real trading will differ
6. **Use FLD for timing** - Cycle detection finds frequency, FLD finds entry points

---

**End of Documentation**
