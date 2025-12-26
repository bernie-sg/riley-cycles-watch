# Phase 2 Requirements - Complete Scraper

## Updated Scope (December 25, 2025)

### Data Sources

1. **Futures Hub** (https://askslim.com/futures-hub/)
   - 18 instruments to scrape (excluding HO, RB, ETH)
   - Technical Details: Cycle Low Dates, Cycle Counts
   - Charts: Weekly + Daily

2. **Equities and ETFs Hub** (location TBD - from dashboard)
   - All stocks and ETFs shown
   - Exclude: VIX
   - Include: SPX, NDX, RUT already in Riley DB
   - Technical Details: Cycle Low Dates, Cycle Counts
   - Charts: Weekly + Daily

### Requirements

#### 1. Human-Like Behavior
- ✅ Random delays between actions (1-3 seconds)
- ✅ Scroll naturally
- ✅ Vary timing
- ✅ Don't trigger bot detection
- ✅ Respect rate limits

#### 2. Data Extraction Per Instrument
- ✅ Cycle Low Dates (Weekly + Daily)
- ✅ Cycle Counts/Dominant Cycle (Weekly + Daily)
- ✅ Weekly chart image
- ✅ Daily chart image

#### 3. Chart Management
- ✅ Download charts to `media/{RILEY_SYMBOL}/`
- ✅ Check if chart is newer than existing
- ✅ Use filename or date to determine freshness
- ✅ Skip download if not updated

#### 4. Database Updates
- ✅ **UPDATE existing records, don't INSERT duplicates**
- ✅ "One truth" - single source of truth per instrument
- ✅ Update cycle_specs table
- ✅ Increment version_num
- ✅ Set source="askSlim"
- ✅ Update both Daily and Weekly timeframes

#### 5. Validation
- ✅ Check all data before marking complete
- ✅ Verify dates are valid
- ✅ Verify cycle lengths are reasonable
- ✅ Verify all instruments scraped
- ✅ Verify charts downloaded
- ✅ Verify database updated

### Issues to Resolve

1. **Page Loading:** Instrument boxes not appearing consistently
   - First screenshot showed instruments
   - Second screenshot blank
   - Need reliable way to load content

2. **Navigation Path:**
   - How to get from dashboard to Futures Hub instruments?
   - How to get from dashboard to Equities/ETFs Hub?
   - Are instruments on main page or individual pages?

3. **Selectors:**
   - How to click on each instrument?
   - Where is "Technical Details" section?
   - How to find cycle data?
   - How to get chart image URLs?

### Proposed Approach

**Option A: Manual Discovery**
1. Run browser in visible mode
2. User shows exact navigation steps
3. Record selectors using DevTools
4. Build scraper from recording

**Option B: Incremental Build**
1. Get ONE instrument working (e.g., SPX)
2. Extract all data for that one
3. Verify database update works
4. Then replicate for all instruments

**Option C: Ask User for Page URLs**
If each instrument has its own page:
- SPX page URL?
- NDX page URL?
- etc.

Then scraper can go directly to each URL instead of navigating from hub.

### Next Steps

Need from user:
1. How do you navigate to see SPX cycle data?
2. Is it on the Futures Hub main page or a separate page?
3. Can you provide a direct URL to SPX technical details?
4. Same questions for Equities/ETFs Hub

Once I understand the navigation, I can build the complete scraper.
