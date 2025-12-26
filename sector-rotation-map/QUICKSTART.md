# Quick Start Guide

## Install & Run (30 seconds)

### macOS/Linux

```bash
cd sector-rotation-map
chmod +x run.sh
./run.sh
```

### Windows

```cmd
cd sector-rotation-map
run.bat
```

### Manual Installation

```bash
cd sector-rotation-map
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Try It Out

1. App opens at `http://localhost:8501`
2. Click "Upload CSV Data" in sidebar
3. Select `examples/mode_b_template.csv`
4. See the RRG chart appear instantly!

## Next Steps

- Try `examples/mode_a_template.csv` to see auto-computation
- Adjust tail length slider
- Toggle tails/labels on/off
- Export chart as PNG
- Download table as CSV

## Get Your Own Data

### Option A: Yahoo Finance (recommended)

```python
import yfinance as yf
import pandas as pd

# Download sector ETF data
symbols = ['SPY', 'XLK', 'XLY', 'XLC', 'XLV', 'XLF', 'XLE', 'XLI', 'XLP', 'XLU', 'XLB', 'XLRE']
data = yf.download(symbols, start='2025-01-01', end='2025-12-31')

# Extract close prices
closes = data['Close'].reset_index()
closes_long = closes.melt(id_vars='Date', var_name='symbol', value_name='close')
closes_long.rename(columns={'Date': 'date'}, inplace=True)

# Save to CSV
closes_long.to_csv('my_sector_data.csv', index=False)
```

### Option B: Manual CSV

Create a CSV with these columns:
- `date` (YYYY-MM-DD)
- `symbol` (e.g., XLK)
- `close` (price)

Save and upload!

## Need Help?

See full documentation in `README.md`
