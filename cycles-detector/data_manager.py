#!/usr/bin/env python3
"""
Data Manager - Wrapper around shared CSV price manager
Maintains backward compatibility with Cycles Detector
"""

import sys
from pathlib import Path

# Add Riley modules to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.modules.marketdata.csv_price_manager import get_price_data


class DataManager:
    def __init__(self, symbol='TLT', data_dir=None):
        """
        Initialize data manager.
        data_dir parameter ignored - always uses shared data/price_history/
        """
        self.symbol = symbol.upper()

    def get_data(self):
        """
        Get price data from shared CSV files.

        Returns:
            Tuple of (prices array, DataFrame)
        """
        return get_price_data(self.symbol)


if __name__ == '__main__':
    # Test the data manager
    print("Testing Data Manager (using shared CSV price manager)")
    print("=" * 50)

    dm = DataManager('SPY')
    prices, df = dm.get_data()

    print(f"\nData summary:")
    print(f"  Total bars: {len(prices)}")
    print(f"  Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"  Latest price: ${prices[-1]:.2f}")
