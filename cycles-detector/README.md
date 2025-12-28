# SIGMA-L Cycle Analysis Web Application

A complete web-based interface for the SIGMA-L cycle analysis system, providing interactive visualization and configuration of market cycle detection algorithms.

## Features

### 🔬 **Advanced Cycle Analysis**
- **Power Spectrum Analysis**: Detect dominant market cycles using original SIGMA-L algorithms
- **Interactive Heatmap**: Visualize cycle strength evolution over time with purple heat mapping
- **Bandpass Filtering**: Generate precise cycle signals with automatic phase detection
- **Peak/Trough Detection**: Mark cycle extremes with automatic detection

### ⚙️ **Configurable Parameters**
- **Window Size**: 1000-5000 bars (default: 4000)
- **Wavelength Range**: Customizable from 50-1200 days
- **Step Size**: Adjustable wavelength scanning resolution
- **Real-time Updates**: Instant recalculation with parameter changes

### 📊 **Interactive Visualizations**
- **Price Chart**: TLT price data with bandpass overlay
- **Bandpass Signal**: Isolated cycle component with marked peaks/troughs
- **Cycle Heatmap**: Time-frequency analysis showing cycle evolution
- **Power Spectrum**: Frequency domain analysis with labeled dominant cycles

### 🎯 **Key Metrics Display**
- Data points loaded and processing window
- Heatmap coverage (years/weeks)
- Selected cycle wavelength and phase
- Top detected cycles with amplitudes

## Quick Start

### Prerequisites
```bash
pip3 install flask numpy scipy matplotlib
```

### Running the Application
```bash
cd webapp
python3 app.py
```

### Access the Interface
Open your browser to: **http://localhost:5001**

## File Structure

```
webapp/
├── app.py                 # Flask backend with SIGMA-L analysis
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Interactive frontend interface
├── algorithms/           # Core SIGMA-L algorithms (copied from parent)
│   ├── heatmap/
│   │   └── heatmap_algo.py
│   └── bandpass/
│       └── sigma_l_bandpass_filter.py
└── tlt_prices.txt        # TLT price data
```

## API Endpoints

### `/api/analyze`
**GET** - Run SIGMA-L analysis with parameters
- `window_size`: Analysis window (default: 4000)
- `min_wavelength`: Minimum cycle length (default: 100)
- `max_wavelength`: Maximum cycle length (default: 800)
- `wavelength_step`: Scanning resolution (default: 5)

### `/api/config`
**GET** - Get configuration options and data info

## Technical Details

### Algorithm Integration
- **Direct Integration**: Uses original algorithms from `algorithms/` folder without modification
- **Consistent Processing**: 4000-bar window ensures objective, repeatable results
- **Phase Optimization**: Cross-correlation method for optimal bandpass alignment

### Data Processing
- **5,828 TLT price points** (~23 years of data)
- **Automatic Date Generation**: Creates timeline from data length
- **Efficient Heatmap**: Pre-calculated for responsive interface
- **JSON API**: Structured data exchange for frontend visualization

### Frontend Technology
- **Plotly.js**: Interactive, responsive charts
- **Modern CSS**: Dark theme optimized for financial analysis
- **Real-time Updates**: Async API calls with loading states
- **Mobile Responsive**: Works on desktop and mobile devices

## Configuration Examples

### Short-term Analysis (2000 bars)
- **Coverage**: ~14.7 years of heatmap
- **Best For**: Recent cycle detection
- **Dominant Cycles**: 345d, 790d, 590d

### Standard Analysis (4000 bars)
- **Coverage**: 7.0 years of heatmap
- **Best For**: Stable, consistent analysis
- **Dominant Cycles**: 630d, 680d, 350d

### Extended Analysis (5000+ bars)
- **Coverage**: 5+ years of heatmap
- **Best For**: Long-term cycle validation
- **Higher Accuracy**: More data for stable detection

## Based on SIGMA-L Theory

This application implements the complete SIGMA-L cycle analysis methodology:

1. **Morlet Wavelet Analysis** with frequency-dependent Q factor
2. **Bandpass Filter Generation** using uniform sine waves
3. **Phase Detection** via cross-correlation optimization
4. **Heatmap Visualization** showing cycle evolution over time
5. **Peak/Trough Detection** for timing market extremes

The web interface provides the same analysis as the standalone Python scripts, but with interactive controls and real-time visualization.

## Development Notes

- **Flask Backend**: Handles analysis requests and serves data
- **Stateless Design**: Each analysis request is independent
- **Error Handling**: Graceful degradation with user feedback
- **Performance Optimized**: Background processing with progress indicators

---

**Access the live application at: http://localhost:5001**