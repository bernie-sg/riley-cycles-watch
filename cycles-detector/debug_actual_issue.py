#!/usr/bin/env python3
"""
Debug script to see what's actually happening with KO 425d
"""
import sys
import numpy as np

sys.path.insert(0, '/Users/bernie/Documents/Cycles Detector/Cycles Detector V14/webapp')

from data_manager import DataManager
from algorithms.bandpass.pure_sine_bandpass import create_pure_sine_bandpass

# Load KO data
dm = DataManager('KO')
prices, df = dm.get_data()

# Use 4000 bars
if len(prices) > 4000:
    prices = prices[-4000:]

print(f"Loaded {len(prices)} bars")
print(f"Testing KO 425d trough alignment...")
print("="*100)

# Call the bandpass function
try:
    result = create_pure_sine_bandpass(
        prices=prices,
        wavelength=425,
        bandwidth_pct=0.10,
        extend_future=700,
        method='actual_price_peaks',
        align_to='trough'
    )

    print(f"\n✅ Function completed successfully")
    print(f"\nResult keys: {result.keys()}")
    print(f"\nBandpass shape: {result['bandpass_normalized'].shape}")
    print(f"Bandpass min: {np.min(result['bandpass_normalized']):.4f}")
    print(f"Bandpass max: {np.max(result['bandpass_normalized']):.4f}")
    print(f"Bandpass has NaN: {np.any(np.isnan(result['bandpass_normalized']))}")
    print(f"Bandpass has Inf: {np.any(np.isinf(result['bandpass_normalized']))}")

    if 'peaks' in result:
        print(f"\nPeaks: {len(result['peaks'])} labels")
        if len(result['peaks']) > 0:
            print(f"  First 5: {result['peaks'][:5]}")
    else:
        print(f"\n⚠️  No 'peaks' in result!")

    if 'troughs' in result:
        print(f"\nTroughs: {len(result['troughs'])} labels")
        if len(result['troughs']) > 0:
            print(f"  First 5: {result['troughs'][:5]}")
    else:
        print(f"\n⚠️  No 'troughs' in result!")

    print(f"\nPhase degrees: {result.get('phase_degrees', 'N/A')}")
    print(f"Method: {result.get('method', 'N/A')}")

except Exception as e:
    print(f"\n❌ Exception occurred:")
    print(f"  {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
