# BANDPASS ALGORITHM - QUICK REFERENCE

## THE ONLY THING YOU NEED TO KNOW

**SIGMA-L Bandpass = Uniform Sine Wave**

```python
bandpass = np.sin(2 * np.pi / wavelength * t)
```

That's it. Nothing more complex.

## To Run:
```bash
python3 sigma_l_bandpass_filter.py --wavelength 260
```

## Files:
- `sigma_l_bandpass_filter.py` - The working implementation
- `bandpass_algo.py` - MA difference method (alternative)
- `BANDPASS_COMPLETE_DOCUMENTATION.md` - Full details

## DO NOT:
- Extract from market data
- Vary amplitude
- Use complex methods
- Modulate based on conditions

## ALWAYS:
- Generate uniform sine wave
- Use constant amplitude (0.01 for display)
- Mark peaks/troughs at regular intervals

**Status**: WORKING - DO NOT CHANGE