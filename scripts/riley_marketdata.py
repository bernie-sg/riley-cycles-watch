#!/usr/bin/env python3
"""
Riley Market Data CLI Wrapper

Quick access to market data collection commands.
"""
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from riley.modules.marketdata.cli import main

if __name__ == '__main__':
    sys.exit(main())
