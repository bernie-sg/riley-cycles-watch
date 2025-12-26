# askSlim to Riley Instrument Mapping

## Futures Hub Instruments

Based on screenshot of https://askslim.com/futures-hub/

### Indexes
| askSlim | Riley | Status |
|---------|-------|--------|
| SPX | ES | ✅ Scrape |
| NDX | NQ | ✅ Scrape |
| RUT | RTY | ✅ Scrape |

### Treasuries
| askSlim | Riley | Status |
|---------|-------|--------|
| TNX | - | ⏭️ Skip (not in Riley DB) |
| /ZB | ZB | ✅ Scrape |
| TLT | - | ⏭️ Skip (not in Riley DB) |
| /ZN | - | ⏭️ Skip (not in Riley DB) |

### Currencies
| askSlim | Riley | Status |
|---------|-------|--------|
| EUR/USD | EURUSD | ✅ Scrape |
| $DXY | DXY | ✅ Scrape |
| USD/JPY | USDJPY | ✅ Scrape |
| AUD/USD | AUDUSD | ✅ Scrape |
| GBP/USD | GBPUSD | ✅ Scrape |

### Metals
| askSlim | Riley | Status |
|---------|-------|--------|
| /GC | GC | ✅ Scrape |
| /SI | SI | ✅ Scrape |
| /PL | PL | ✅ Scrape |
| /HG | HG | ✅ Scrape |

### Energies
| askSlim | Riley | Status |
|---------|-------|--------|
| /CL | CL | ✅ Scrape |
| /HO | - | ❌ SKIP (user excluded) |
| /RB | - | ❌ SKIP (user excluded) |
| /NG | NG | ✅ Scrape |

### Grains/Softs
| askSlim | Riley | Status |
|---------|-------|--------|
| /ZC | ZC | ✅ Scrape |
| /ZS | ZS | ✅ Scrape |
| /ZW | ZW | ✅ Scrape |

## Riley Instruments Not on askSlim Futures Hub

| Riley | Notes |
|-------|-------|
| BTC | Bitcoin - might be on different page or not available |
| NVDA | Nvidia stock - not a futures contract |
| XLE | Energy sector ETF - not a futures contract |
| USDCAD | Not shown on Futures Hub page |

## Totals

- **askSlim instruments:** 27 total
- **To scrape:** 18 instruments
- **Skip (not in Riley):** 4 (TNX, TLT, /ZN, + any others not mapped)
- **Skip (user excluded):** 2 (/HO, /RB)
- **Skip (not shown):** 3 (assuming ETH not on page, BTC, NVDA, XLE, USDCAD)

## Symbol Mapping Dictionary

```python
ASKSLIM_TO_RILEY = {
    # Indexes
    "SPX": "ES",
    "NDX": "NQ",
    "RUT": "RTY",

    # Treasuries
    "/ZB": "ZB",

    # Currencies
    "EUR/USD": "EURUSD",
    "$DXY": "DXY",
    "USD/JPY": "USDJPY",
    "AUD/USD": "AUDUSD",
    "GBP/USD": "GBPUSD",

    # Metals
    "/GC": "GC",
    "/SI": "SI",
    "/PL": "PL",
    "/HG": "HG",

    # Energies
    "/CL": "CL",
    "/NG": "NG",

    # Grains
    "/ZC": "ZC",
    "/ZS": "ZS",
    "/ZW": "ZW",
}

# Instruments to skip
SKIP_INSTRUMENTS = {
    "/HO",  # Heating oil (user excluded)
    "/RB",  # RBOB gasoline (user excluded)
    "ETH",  # Ethereum (user excluded)
    "TNX",  # 10-year Treasury note (not in Riley DB)
    "TLT",  # Treasury bond ETF (not in Riley DB)
    "/ZN",  # 10-year Treasury futures (not in Riley DB)
}
```

## Chart Download Requirements

For each instrument, download:

1. **Weekly Chart:**
   - Location: Under "Weekly" section
   - Filename format: TBD (check askSlim)
   - Save to: `media/{RILEY_SYMBOL}/weekly_YYYYMMDD.png`
   - Check: Only download if newer than existing

2. **Daily Chart:**
   - Location: Under "Daily" section
   - Filename format: TBD (check askSlim)
   - Save to: `media/{RILEY_SYMBOL}/daily_YYYYMMDD.png`
   - Check: Only download if newer than existing

## Data to Extract Per Instrument

```json
{
  "askslim_symbol": "SPX",
  "riley_symbol": "ES",
  "cycle_data": {
    "weekly": {
      "low_date": "2026-01-04",
      "dominant_cycle": 37,
      "chart_url": "https://...",
      "chart_filename": "weekly_20251225.png"
    },
    "daily": {
      "low_date": "2025-12-28",
      "dominant_cycle": 26,
      "chart_url": "https://...",
      "chart_filename": "daily_20251225.png"
    }
  },
  "scraped_at": "2025-12-25T12:00:00Z"
}
```
