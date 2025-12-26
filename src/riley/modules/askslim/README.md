# askSlim Integration Module

Automated login and session management for askSlim.com (Phase 1).

## Purpose

This module provides authenticated access to askSlim.com to scrape cycle data and update the Riley Cycles Watch database. It uses Playwright for browser automation to handle the login flow and maintain session state.

## Phase 1 Status

✅ **Complete**: Login + Session Persistence + Smoke Test
🔲 **Phase 2**: Data scraping and database updates (not yet implemented)

## Architecture

```
src/riley/modules/askslim/
├── __init__.py              # Module marker
├── askslim_login.py         # Performs login, saves session state
├── askslim_smoketest.py     # Verifies saved session is valid
├── askslim_run_daily.py     # Daily job stub (Phase 2: scraping)
├── storage_state.json       # Saved auth state (gitignored)
└── README.md               # This file

artifacts/askslim/           # Debug artifacts
├── login_success.png        # Screenshot on successful login
├── login_failed.png         # Screenshot if login fails
├── login_failed.html        # Page HTML if login fails
└── smoketest_*.png          # Smoke test screenshots
```

## Installation

### 1. Install Dependencies

```bash
cd "/Users/bernie/Documents/AI/Riley Project"
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Credentials

Create a `.env` file in the project root:

```bash
cp .env.example .env
# Edit .env and add your askSlim credentials
```

Required variables:
- `ASKSLIM_USERNAME` - Your askSlim member email
- `ASKSLIM_PASSWORD` - Your askSlim password

Optional variables:
- `ASKSLIM_BASE_URL` - Default: `https://askslim.com`
- `ASKSLIM_HEADLESS` - Default: `false` (set to `true` for automated runs)
- `ASKSLIM_STORAGE_STATE_PATH` - Custom path for session storage

## Usage

### Step 1: Login (One-Time or When Session Expires)

Run the login module to authenticate and save session state:

```bash
python -m src.riley.modules.askslim.askslim_login
```

**What it does:**
1. Launches Chromium browser (visible by default)
2. Navigates to askslim.com/login
3. Fills in credentials from `.env`
4. Submits login form
5. Waits for successful login (looks for "Logout", "My Feed", etc.)
6. Saves authenticated session to `storage_state.json`
7. Takes success screenshot

**On failure:**
- Saves screenshot to `artifacts/askslim/login_failed.png`
- Saves HTML to `artifacts/askslim/login_failed.html`
- Exits with error code 1

**Expected output:**
```
Starting askSlim login...
Base URL: https://askslim.com
Username: your_email@example.com
Headless mode: False
Storage state path: .../storage_state.json

Navigating to https://askslim.com...
Looking for login link...
Found login link with selector: text=Login
Current URL after clicking login: https://askslim.com/login
Filling login credentials...
Found username field: input[name='email']
Found password field: input[type='password']
Submitting login form...
Found submit button: button[type='submit']
Waiting for login to complete...
Current URL after login attempt: https://askslim.com/feed
✓ Login successful! Found indicator: text=My Feed

Saving session state to: .../storage_state.json
✓ Session state saved successfully!
Success screenshot: .../login_success.png

============================================================
LOGIN COMPLETE
============================================================
Session state: .../storage_state.json
You can now run askslim_smoketest.py to verify the session
```

### Step 2: Verify Session (Smoke Test)

Verify that the saved session is still valid:

```bash
python -m src.riley.modules.askslim.askslim_smoketest
```

**What it does:**
1. Loads `storage_state.json`
2. Launches browser with saved session
3. Navigates to askslim.com
4. Verifies logged-in indicators are present
5. Takes success screenshot

**Expected output:**
```
Loading session state from: .../storage_state.json
Base URL: https://askslim.com
Headless mode: True

Navigating to https://askslim.com...
Current URL: https://askslim.com/
✓ Session is valid! Found indicator: text=Logout
Success screenshot: .../smoketest_success.png

============================================================
SMOKE TEST PASSED
============================================================
Session state is valid and authenticated
OK
```

### Step 3: Daily Run (Phase 1 Stub)

Run the daily scraping job (currently just verifies session):

```bash
python -m src.riley.modules.askslim.askslim_run_daily
```

**Current behavior (Phase 1):**
- Verifies session is valid
- Prints placeholder messages for Phase 2 scraping
- Exits successfully

**Phase 2 (not yet implemented):**
- Navigate to askSlim pages
- Extract cycle data (anchors, lengths, sources)
- Parse dates and metadata
- Update Riley database
- Log results

## Logged-In Detection

The module uses multiple selectors to detect successful login:

- `text=Logout` / `text=Log Out` / `text=Sign Out`
- `text=My Feed` / `text=WorkBench`
- `.user-menu` / `.logged-in`

If askSlim changes their UI, update the `logged_in_indicators` list in both `askslim_login.py` and `askslim_smoketest.py`.

## Session State Storage

Session state is saved to `storage_state.json` (gitignored) and includes:
- Cookies
- Local storage
- Session storage
- Other browser auth state

This file allows subsequent runs to bypass login by reusing the authenticated session.

**When to re-login:**
- Session expires (typically after some hours/days)
- Smoke test fails
- askSlim requires re-authentication

## Security Notes

✅ **Legal**: This is for your own paid member account only
✅ **Rate Limited**: Browser automation is human-like and slow
✅ **Credentials**: Stored in `.env` (gitignored), never in code
✅ **Session State**: Gitignored, never committed

🚫 **Do NOT:**
- Share credentials or session state files
- Commit `.env` or `storage_state.json` to git
- Attempt to bypass CAPTCHA or MFA programmatically
- Scrape content beyond your membership level

## Troubleshooting

### Login fails with "Could not find login link"

The homepage selectors may have changed. Check:
1. `artifacts/askslim/login_failed.png` - visual state
2. `artifacts/askslim/login_failed.html` - page source
3. Update `login_selectors` in `askslim_login.py`

### Login submits but "no logged-in indicators found"

askSlim may have changed their post-login UI. Update:
1. `logged_in_indicators` in `askslim_login.py`
2. `logged_in_indicators` in `askslim_smoketest.py`

### "Session state file not found"

Run `askslim_login.py` first to create the session.

### Smoke test fails

Session has expired. Re-run `askslim_login.py`.

### MFA/CAPTCHA required

The module does NOT handle MFA or CAPTCHA automatically. If askSlim requires MFA:
1. Run `askslim_login.py` with `ASKSLIM_HEADLESS=false`
2. Complete MFA manually in the browser window
3. The session state will be saved after successful login
4. Future runs will reuse the authenticated session

## Files Reference

### askslim_login.py

**Purpose**: Perform browser login and save session state

**Usage**: `python -m src.riley.modules.askslim.askslim_login`

**Environment Variables**:
- `ASKSLIM_USERNAME` (required)
- `ASKSLIM_PASSWORD` (required)
- `ASKSLIM_BASE_URL` (optional, default: https://askslim.com)
- `ASKSLIM_HEADLESS` (optional, default: false)
- `ASKSLIM_STORAGE_STATE_PATH` (optional)

**Exit Codes**:
- `0` - Login successful
- `1` - Login failed

### askslim_smoketest.py

**Purpose**: Verify saved session is valid

**Usage**: `python -m src.riley.modules.askslim.askslim_smoketest`

**Exit Codes**:
- `0` - Session valid
- `1` - Session invalid or expired

### askslim_run_daily.py

**Purpose**: Daily scraping job (Phase 1: stub, Phase 2: actual scraping)

**Usage**: `python -m src.riley.modules.askslim.askslim_run_daily`

**Current Behavior**: Verifies session only

**Future Behavior (Phase 2)**: Scrape cycle data and update database

## Next Steps (Phase 2)

1. Identify askSlim pages with cycle data
2. Extract cycle anchors, lengths, and sources
3. Parse dates into Riley format
4. Map askSlim instruments to Riley canonical symbols
5. Update `cycle_specs` table in Riley database
6. Add logging and error handling
7. Schedule daily runs (cron or n8n)

## License

Part of the Riley Cycles Watch project.
