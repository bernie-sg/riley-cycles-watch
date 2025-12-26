# 📊 Sector Rotation Map (RRG-Style)

An interactive Relative Rotation Graph (RRG) visualization for analyzing sector rotation patterns. Built with Python, Streamlit, and Plotly.

![Sector Rotation Map](https://via.placeholder.com/1200x700.png?text=Sector+Rotation+Map)

## Features

- **Interactive RRG Chart** with 4 quadrants (Improving, Leading, Weakening, Lagging)
- **Historical Tails** showing sector movement over time
- **Two Data Modes**:
  - Mode A: Automatically compute RRG metrics from OHLCV data
  - Mode B: Use precomputed RS-Ratio and RS-Momentum values
- **Customizable Parameters**:
  - Tail length (weeks)
  - Smoothing periods
  - Lookback windows
  - Date range selection
- **Export Capabilities**:
  - Chart as PNG
  - Table data as CSV
- **US Sector ETF Support** (XLK, XLY, XLC, XLV, XLF, XLE, XLI, XLP, XLU, XLB, XLRE)

## Quick Start

### Installation

1. Clone or download this project:
```bash
cd sector-rotation-map
```

2. Create virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Data Formats

### Mode A: OHLCV Data (Auto-Compute RRG)

Upload a CSV with historical price data. The app will compute RS-Ratio and RS-Momentum.

**Required Columns:**
- `date` (YYYY-MM-DD format)
- `symbol` (e.g., XLK, SPY, QQQ)
- `close` (closing price)

**Optional Columns:**
- `open`, `high`, `low`, `volume`

**Example:**
```csv
date,symbol,close
2025-12-01,SPY,450.25
2025-12-01,XLK,185.50
2025-12-01,XLY,165.75
2025-12-08,SPY,452.30
2025-12-08,XLK,188.20
2025-12-08,XLY,166.10
```

See `examples/mode_a_template.csv` for a complete example.

### Mode B: Precomputed Metrics

Upload a CSV with pre-calculated RS-Ratio and RS-Momentum values.

**Required Columns:**
- `date` (YYYY-MM-DD format)
- `symbol` (e.g., XLK, SPY)
- `rs_ratio` (relative strength ratio, typically around 100)
- `rs_momentum` (momentum of RS ratio, typically around 100)

**Example:**
```csv
date,symbol,rs_ratio,rs_momentum
2025-12-01,XLK,102.50,101.25
2025-12-01,XLY,98.75,99.50
2025-12-08,XLK,103.20,102.10
2025-12-08,XLY,98.30,98.95
```

See `examples/mode_b_template.csv` for a complete example.

## How It Works

### RRG Methodology (Mode A)

When you upload OHLCV data, the app computes RRG metrics using this methodology:

1. **Relative Strength (RS)**: `RS = close(sector) / close(benchmark)`
2. **Smoothed RS**: Apply EMA smoothing to RS (default: 10 periods)
3. **RS-Ratio**: `100 * (smoothed_rs / rolling_mean(smoothed_rs, ratio_lookback))`
4. **RS-Momentum**: `100 * (rs_ratio / rolling_mean(rs_ratio, momentum_lookback))`

Values around 100 represent neutral positioning. Values > 100 indicate strength, values < 100 indicate weakness.

### Quadrant Interpretation

- **Leading (Top-Right)**: High relative strength, positive momentum
  - Sectors outperforming with accelerating momentum
  - Continue to monitor for peak signals

- **Improving (Top-Left)**: Low relative strength, positive momentum
  - Sectors recovering from weakness
  - Early rotation candidates - may move to Leading

- **Weakening (Bottom-Right)**: High relative strength, negative momentum
  - Sectors still strong but losing momentum
  - May rotate to Lagging quadrant - consider reducing exposure

- **Lagging (Bottom-Left)**: Low relative strength, negative momentum
  - Sectors underperforming with declining momentum
  - Watch for bottoming signals to rotate to Improving

## Usage Guide

### 1. Upload Data

Click "Upload CSV Data" in the sidebar and select your file. The app will auto-detect Mode A or Mode B.

### 2. Configure Settings

**Benchmark Symbol**: Select the benchmark (default: SPY)

**Tail Length**: Choose how many weeks of history to display (default: 5)

**End Date**: Select the analysis date (default: latest date in data)

**Toggles**:
- Show Tails: Display historical path
- Show Labels: Display sector symbols on chart

### 3. Mode A Parameters (if applicable)

Fine-tune RRG calculations:
- **RS Smoothing Period**: EMA smoothing (default: 10)
- **RS-Ratio Lookback**: Rolling mean period (default: 10)
- **RS-Momentum Lookback**: Rolling mean period (default: 10)

### 4. Analyze Results

- **Chart**: Visual representation of sector positions and trends
- **Table**: Detailed metrics for each sector
- **Export**: Save chart as PNG or table as CSV

## US Sector ETFs

| Symbol | Sector Name |
|--------|-------------|
| XLK | Technology |
| XLY | Consumer Discretionary |
| XLC | Communication Services |
| XLV | Health Care |
| XLF | Financials |
| XLE | Energy |
| XLI | Industrials |
| XLP | Consumer Staples |
| XLU | Utilities |
| XLB | Materials |
| XLRE | Real Estate |

## Project Structure

```
sector-rotation-map/
├── app.py                  # Main Streamlit application
├── rrg/                    # RRG computation package
│   ├── __init__.py
│   ├── constants.py        # Sector lists, colors, defaults
│   ├── data.py            # Data loading and validation
│   ├── compute.py         # RRG metric calculations
│   └── chart.py           # Plotly chart generation
├── examples/              # Example CSV templates
│   ├── mode_a_template.csv
│   └── mode_b_template.csv
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Requirements

- Python 3.8+
- streamlit >= 1.28.0
- plotly >= 5.17.0
- pandas >= 2.0.0
- numpy >= 1.24.0
- kaleido >= 0.2.1 (for PNG export)

## Tips & Best Practices

1. **Data Quality**: Ensure your data has no gaps or missing dates for best results

2. **Benchmark Selection**: Use a broad market index (SPY, VTI) for sector analysis

3. **Tail Length**:
   - Shorter tails (3-5 weeks): Recent rotation signals
   - Longer tails (8-12 weeks): Trend identification

4. **Parameter Tuning**:
   - Lower smoothing values: More sensitive to changes
   - Higher smoothing values: Smoother, less noise

5. **Interpretation**:
   - Focus on direction of movement, not just position
   - Sectors crossing quadrants indicate rotation
   - Tails curving back suggest reversal patterns

## Troubleshooting

**Error: "CSV must contain either Mode A or Mode B columns"**
- Check your CSV has the required columns
- Ensure column names are lowercase or match exactly

**Chart shows no data**
- Verify date range includes your data
- Check that benchmark symbol exists in your data
- Ensure sufficient history for tail length

**Export button not working**
- Make sure kaleido is installed: `pip install kaleido`
- Try restarting the Streamlit app

## License

This project is provided as-is for educational and analysis purposes.

## Credits

Built with:
- [Streamlit](https://streamlit.io/)
- [Plotly](https://plotly.com/)
- [Pandas](https://pandas.pydata.org/)

RRG methodology inspired by the Relative Rotation Graph concept developed by Julius de Kempenaer.

## Support

For issues or questions:
1. Check this README
2. Review example CSV templates
3. Verify data format matches requirements

---

**Happy Analyzing! 📈**
