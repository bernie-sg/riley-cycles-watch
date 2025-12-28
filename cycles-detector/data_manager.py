#!/usr/bin/env python3
"""
Data Manager - Auto-download and update TLT price history
"""

import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

class DataManager:
    def __init__(self, symbol='TLT', data_dir='.'):
        self.symbol = symbol
        self.data_dir = data_dir
        self.csv_file = os.path.join(data_dir, f'{symbol.lower()}_history.csv')
        self.txt_file = os.path.join(data_dir, f'{symbol.lower()}_prices.txt')

    def get_data(self):
        """
        Main entry point - returns price array ready for analysis
        1. Check if CSV exists
        2. If not, download full history
        3. If yes, check if up-to-date and update if needed
        4. Return price array
        """
        if not os.path.exists(self.csv_file):
            print(f"📥 No history file found. Downloading full {self.symbol} history...")
            self._download_full_history()
        else:
            print(f"✓ Found existing history file")
            self._update_if_needed()

        # Load CSV and return prices
        df = pd.read_csv(self.csv_file, parse_dates=['Date'])
        prices = df['Close'].values

        print(f"✓ Loaded {len(prices)} price bars ({df['Date'].min().date()} to {df['Date'].max().date()})")

        # Also save to .txt for backward compatibility
        np.savetxt(self.txt_file, prices)

        return prices, df

    def _download_full_history(self):
        """Download complete history from Yahoo Finance"""
        try:
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(period='max')

            if df.empty:
                raise ValueError(f"No data returned for symbol '{self.symbol}'. Please check if the ticker symbol is correct.")

            # Keep only Date and Close
            df = df[['Close']].reset_index()
            # Convert to date objects (strip timezone and time)
            df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None).dt.date

            # Save to CSV
            df.to_csv(self.csv_file, index=False)
            print(f"✓ Downloaded {len(df)} bars to {self.csv_file}")
        except Exception as e:
            raise ValueError(f"Failed to download data for '{self.symbol}': {str(e)}. Common ticker symbols: AAPL, MSFT, GOOGL, FDX (FedEx), UPS")

    def _update_if_needed(self):
        """Check if data is current and update if needed"""
        df = pd.read_csv(self.csv_file)
        # Convert Date column, handling both string and datetime formats
        df['Date'] = pd.to_datetime(df['Date'])
        last_date = df['Date'].max()
        if hasattr(last_date, 'date'):
            last_date = last_date.date()
        today = datetime.now().date()

        # Check if we're missing recent data (more than 1 day old)
        if last_date < today - timedelta(days=1):
            print(f"📥 Data is outdated (last: {last_date}). Updating...")

            # Download from day after last_date to today
            ticker = yf.Ticker(self.symbol)
            start_date = last_date + timedelta(days=1)
            new_data = ticker.history(start=start_date.strftime('%Y-%m-%d'))

            if len(new_data) > 0:
                # Keep only Date and Close
                new_data = new_data[['Close']].reset_index()
                # Convert to date objects (strip timezone and time)
                new_data['Date'] = pd.to_datetime(new_data['Date']).dt.tz_localize(None).dt.date

                # Ensure existing df also has date objects (not Timestamps)
                df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None).dt.date

                # Append to existing data
                df = pd.concat([df, new_data], ignore_index=True)
                df = df.drop_duplicates(subset=['Date'], keep='last')
                df = df.sort_values('Date').reset_index(drop=True)

                # Save updated CSV
                df.to_csv(self.csv_file, index=False)
                print(f"✓ Added {len(new_data)} new bars (now {len(df)} total)")
            else:
                print(f"✓ No new data available (market closed or weekend)")
        else:
            print(f"✓ Data is current (last update: {last_date})")

if __name__ == '__main__':
    # Test the data manager
    print("Testing Data Manager")
    print("=" * 50)

    dm = DataManager('TLT')
    prices, df = dm.get_data()

    print(f"\nData summary:")
    print(f"  Total bars: {len(prices)}")
    print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"  Latest price: ${prices[-1]:.2f}")
