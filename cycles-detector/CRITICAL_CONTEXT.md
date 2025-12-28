# CRITICAL CONTEXT - READ BEFORE ANY WORK

## THE FUNDAMENTAL PROBLEM

The codebase had a systemic bug where ALL wavelengths were being divided by 1.451 (calendar/trading day conversion). This is **WRONG** because:

1. Yahoo Finance data is already in trading days
2. Users specify wavelengths in trading days
3. The bandpass filter expects wavelengths in trading days
4. Dividing by 1.451 creates sine waves with WRONG wavelengths

Example of the bug:
- User requests AMD 420d cycle
- Code divides: 420 / 1.451 = 289 trading days
- Sine wave has peaks 289 days apart instead of 420 days
- **COMPLETELY WRONG**

## THE FIX

**REMOVED ALL 1.451 CONVERSIONS**

The data flow is:
```
Yahoo Finance (trading days)
  → User requests wavelength (trading days)
  → Bandpass filter (trading days)
  → Frontend display (trading days)
```

NO CONVERSIONS NEEDED. Everything is in trading days.

## PRODUCTION-READY CODE RULES

1. **NO HACKS**: Do not add conditionals, smoothing, or special cases for different wavelengths
2. **ONE CODE PATH**: The same detection algorithm must work for ALL cycles
3. **TEST EVERYTHING**: Before claiming "it works", test:
   - Multiple instruments (10+)
   - All cycles for each instrument
   - Verify wavelength spacing between peaks
   - Verify dates align to actual sine wave peaks
   - Verify Y-values at ±20

4. **CONSISTENCY**: The code that works for 420d must work for 380d, 515d, 590d, etc.

## PEAK/TROUGH DETECTION

Frontend detection algorithm (in index.html):
```javascript
const peakIndices = findPeaks(scaledBandpass, wavelength);
const troughIndices = findTroughs(scaledBandpass, wavelength);
```

This uses:
- Distance parameter: `wavelength / 4`
- Detects from displayed (scaled) bandpass
- No smoothing, no conditionals, no special cases

## BANDPASS GENERATION

Backend (pure_sine_bandpass.py):
```python
omega = 2 * np.pi / wavelength  # Use input wavelength EXACTLY
sine_wave = amplitude * np.sin(omega * t + phase_offset)
```

The wavelength parameter is in trading days. No conversion.

## TESTING CHECKLIST

Before claiming anything is "done":

- [ ] Test 10+ instruments
- [ ] Test ALL cycles for each instrument
- [ ] Verify peak spacing matches wavelength (±15% tolerance)
- [ ] Verify dates are at actual sine wave peaks
- [ ] Verify Y-values at ±20
- [ ] Verify labels appear on screen
- [ ] Verify no missing labels
- [ ] Test on both short (380d) and long (590d) wavelengths

## WHAT NOT TO DO

❌ Add smoothing for wavelengths > 500
❌ Use backend peaks with phase adjustment
❌ Add fallback to different detection algorithm
❌ Add special cases for specific instruments
❌ Add conditionals based on wavelength
❌ Convert wavelengths by 1.451 anywhere
❌ Claim "it works" without comprehensive testing

## WHAT TO DO

✅ Use ONE detection algorithm for ALL cycles
✅ Generate sine waves with EXACT requested wavelength
✅ Detect peaks from displayed bandpass
✅ Test comprehensively before reporting completion
✅ Remove any code that doesn't work
✅ Write production-ready, maintainable code

## THE USER'S EXPLICIT REQUIREMENTS

"I want production-ready code. I want consistency that will work every single time, and not just one instrument or one cycle."

"Why can't you fucking look at the code that actually works and then use it consistently throughout?"

"Don't keep telling me the problem - I know there's a problem. From here on, I want you to be able to run the test yourself. Run it. And then until it's actually fixed, you come and tell me it's fixed."

**DO NOT REPORT COMPLETION UNTIL EVERYTHING IS TESTED AND VERIFIED.**
