#!/usr/bin/env python3
"""
askSlim Complete Scraper - Phase 2
Scrapes Futures Hub and Equities/ETFs Hub for cycle data and charts.
"""

import os
import sys
import time
import random
import sqlite3
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Import Riley database
# Add project root to path (5 levels up from this file)
project_root_for_import = Path(__file__).parent.parent.parent.parent.parent
if str(project_root_for_import) not in sys.path:
    sys.path.insert(0, str(project_root_for_import))

from src.riley.database import Database

# Load environment variables
load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
ASKSLIM_HEADLESS = os.getenv("ASKSLIM_HEADLESS", "true").lower() == "true"

DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
DB_PATH = PROJECT_ROOT / "db" / "riley.sqlite"
MEDIA_PATH = PROJECT_ROOT / "media"
MEDIA_PATH.mkdir(parents=True, exist_ok=True)

# Instrument mapping: askSlim symbol -> Riley canonical symbol
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

# Skip these instruments
SKIP_INSTRUMENTS = {"/HO", "/RB", "ETH", "TNX", "TLT", "/ZN"}


def human_delay(min_sec=1.0, max_sec=3.0):
    """Random delay to simulate human behavior."""
    time.sleep(random.uniform(min_sec, max_sec))


def parse_askslim_date(date_str):
    """Parse MM/DD/YY to YYYY-MM-DD."""
    try:
        dt = datetime.strptime(date_str.strip(), "%m/%d/%y")
        return dt.strftime("%Y-%m-%d")
    except:
        return None


def parse_cycle_bars(bars_str):
    """Extract integer from '37 bars' format."""
    try:
        return int(bars_str.strip().split()[0])
    except:
        return None


def update_instrument_analysis(riley_symbol, directional_bias, video_url):
    """
    Update instrument-level analysis data (directional bias, video URL).

    Args:
        riley_symbol: Canonical symbol (e.g., "ES")
        directional_bias: "Bullish", "Bearish", or "Neutral"
        video_url: YouTube URL or None
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Get instrument_id
        cursor.execute("""
            SELECT instrument_id FROM instruments
            WHERE canonical_symbol = ?
        """, (riley_symbol,))

        instrument = cursor.fetchone()
        if not instrument:
            print(f"  ⚠ Instrument {riley_symbol} not found - skipping analysis update")
            return False

        instrument_id = instrument[0]

        # Check if analysis exists (active records only)
        cursor.execute("""
            SELECT analysis_id, version FROM instrument_analysis
            WHERE instrument_id = ? AND status = 'ACTIVE'
            ORDER BY version DESC LIMIT 1
        """, (instrument_id,))

        existing = cursor.fetchone()

        if existing:
            # Mark old record as superseded
            old_analysis_id, old_version = existing
            new_version = old_version + 1

            cursor.execute("""
                UPDATE instrument_analysis
                SET status = 'SUPERSEDED', updated_at = datetime('now')
                WHERE analysis_id = ?
            """, (old_analysis_id,))

            # Insert new record
            cursor.execute("""
                INSERT INTO instrument_analysis (
                    instrument_id, directional_bias, video_url,
                    source, version, status, created_at, updated_at
                ) VALUES (?, ?, ?, 'askSlim', ?, 'ACTIVE', datetime('now'), datetime('now'))
            """, (instrument_id, directional_bias, video_url, new_version))

            print(f"  ✓ Updated {riley_symbol} analysis: v{old_version} → v{new_version}")
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO instrument_analysis (
                    instrument_id, directional_bias, video_url,
                    source, version, status, created_at, updated_at
                ) VALUES (?, ?, ?, 'askSlim', 1, 'ACTIVE', datetime('now'), datetime('now'))
            """, (instrument_id, directional_bias, video_url))

            print(f"  ✓ Inserted {riley_symbol} analysis: new record")

        conn.commit()
        return True

    except Exception as e:
        print(f"  ✗ Analysis database error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()


def update_riley_database(riley_symbol, timeframe, cycle_date, cycle_length, support_level=None, resistance_level=None):
    """
    Update Riley database with cycle data.
    One truth: UPDATE existing, don't INSERT duplicates.

    Args:
        riley_symbol: Canonical symbol (e.g., "ES")
        timeframe: "W" for weekly or "D" for daily
        cycle_date: Anchor date (YYYY-MM-DD)
        cycle_length: Cycle length in bars
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Convert timeframe from "W"/"D" to "WEEKLY"/"DAILY"
        tf_full = "WEEKLY" if timeframe == "W" else "DAILY"

        # Get instrument_id from canonical symbol
        cursor.execute("""
            SELECT instrument_id FROM instruments
            WHERE canonical_symbol = ?
        """, (riley_symbol,))

        instrument = cursor.fetchone()
        if not instrument:
            print(f"  ⚠ Instrument {riley_symbol} not found in database - skipping")
            return False

        instrument_id = instrument[0]

        # NO VERSIONING: Delete old record and insert new one with version=1
        # askSlim always has the latest data - we don't keep history

        # Delete any existing cycle spec for this instrument/timeframe
        cursor.execute("""
            DELETE FROM cycle_specs
            WHERE instrument_id = ? AND timeframe = ? AND source = 'askSlim'
        """, (instrument_id, tf_full))

        deleted_count = cursor.rowcount

        # Insert new record (always version=1)
        cursor.execute("""
            INSERT INTO cycle_specs (
                instrument_id, timeframe, anchor_input_date_label,
                cycle_length_bars, source, version, status,
                window_minus_bars, window_plus_bars, prewindow_lead_bars,
                support_level, resistance_level,
                created_at, updated_at, median_input_date_label
            ) VALUES (?, ?, ?, ?, ?, 1, 'ACTIVE', 3, 3, 2, ?, ?,
                datetime('now'), datetime('now'), ?)
        """, (instrument_id, tf_full, cycle_date, cycle_length, "askSlim",
              support_level, resistance_level, cycle_date))

        if deleted_count > 0:
            print(f"  ✓ Updated {riley_symbol} {tf_full} (replaced old record)")
        else:
            print(f"  ✓ Inserted {riley_symbol} {tf_full} (new record)")

        conn.commit()
        return True

    except Exception as e:
        print(f"  ✗ Database error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()


def download_chart(modal_context, page, riley_symbol, timeframe):
    """
    Download chart image if newer than existing.
    Args:
        modal_context: The modal context (page or iframe) where image is
        page: Main page object for making requests
        riley_symbol: Riley canonical symbol (e.g., "ES")
        timeframe: "WEEKLY" or "DAILY"
    Returns: True if downloaded, False if skipped/error
    """
    try:
        # Wait for chart to load
        human_delay(1, 2)

        # Find all images in the modal and pick the largest one (likely the chart)
        images = modal_context.query_selector_all("img")

        # Filter for valid image sources (Amazon S3, CDN, etc.)
        chart_img = None
        max_size = 0

        for img in images:
            img_src = img.get_attribute("src")
            if not img_src:
                continue

            # Skip small icons, logos, etc.
            if any(skip in img_src.lower() for skip in ["logo", "icon", "avatar", "button"]):
                continue

            # Prioritize images from CDN or S3
            if any(cdn in img_src.lower() for cdn in ["amazonaws", "cloudfront", "cdn", "s3"]):
                # Try to get image dimensions
                try:
                    width = img.evaluate("el => el.naturalWidth")
                    height = img.evaluate("el => el.naturalHeight")
                    size = width * height
                    if size > max_size:
                        max_size = size
                        chart_img = img
                        img_src_selected = img_src
                except:
                    chart_img = img
                    img_src_selected = img_src

        if not chart_img:
            # Fallback: just grab the first sizeable image
            for img in images:
                img_src = img.get_attribute("src")
                if img_src and "http" in img_src:
                    try:
                        width = img.evaluate("el => el.naturalWidth")
                        if width > 400:  # Reasonable chart width
                            chart_img = img
                            img_src_selected = img_src
                            break
                    except:
                        pass

        if not chart_img:
            print(f"  ⚠ No chart image found for {timeframe}")
            return False

        img_src = chart_img.get_attribute("src")
        if not img_src:
            return False

        # Make absolute URL
        if img_src.startswith("//"):
            img_src = "https:" + img_src
        elif img_src.startswith("/"):
            img_src = ASKSLIM_BASE_URL + img_src

        print(f"  → Chart URL: {img_src[:80]}...")

        # Create media folder for instrument (categorized by askslim)
        inst_media_path = MEDIA_PATH / riley_symbol / "askslim"
        inst_media_path.mkdir(parents=True, exist_ok=True)

        # Filename with date
        today = datetime.now().strftime("%Y%m%d")
        filename = f"{timeframe.lower()}_{today}.png"
        filepath = inst_media_path / filename

        # Check if already exists
        if filepath.exists():
            print(f"  ⏭ Chart already downloaded: {filename}")
            return False

        # Download image
        response = page.request.get(img_src)
        if response.ok:
            with open(filepath, 'wb') as f:
                f.write(response.body())
            print(f"  ✓ Downloaded chart: {filename}")

            # Track in database (use relative path from project root)
            try:
                db = Database()
                # Store relative path: media/SYMBOL/askslim/filename.png
                relative_path = filepath.relative_to(PROJECT_ROOT)
                db.insert_media_file(
                    instrument_symbol=riley_symbol,
                    category='askslim',
                    timeframe=timeframe,
                    file_path=str(relative_path),
                    file_name=filename,
                    upload_date=datetime.now().strftime("%Y-%m-%d"),
                    source='scraper'
                )
                db.close()
                print(f"  ✓ Tracked in database")
            except Exception as e:
                print(f"  ⚠ Database tracking failed: {e}")

            return True
        else:
            print(f"  ✗ Failed to download chart: {response.status}")
            return False

    except Exception as e:
        print(f"  ✗ Chart download error: {e}")
        return False


def scrape_instrument(page, askslim_symbol, iframe):
    """
    Scrape one instrument from Futures Hub.
    Args:
        page: Main page object
        askslim_symbol: Symbol on askSlim (e.g., "SPX")
        iframe: The iframe containing the instruments
    Returns: dict with cycle data or None if failed
    """
    riley_symbol = ASKSLIM_TO_RILEY.get(askslim_symbol)
    if not riley_symbol:
        print(f"⏭ Skipping {askslim_symbol} (not in Riley DB)")
        return None

    print(f"\n{'='*60}")
    print(f"Scraping: {askslim_symbol} → {riley_symbol}")
    print(f"{'='*60}")

    # Delete old askslim charts before scraping new ones
    try:
        db = Database()
        today = datetime.now().strftime("%Y-%m-%d")
        deleted_count = 0
        deleted_count += db.delete_old_askslim_media(riley_symbol, 'WEEKLY', today)
        deleted_count += db.delete_old_askslim_media(riley_symbol, 'DAILY', today)
        if deleted_count > 0:
            print(f"🗑 Deleted {deleted_count} old askslim chart(s)")
        db.close()
    except Exception as e:
        print(f"⚠ Failed to clean old media: {e}")

    try:
        # Click on instrument button INSIDE the iframe
        human_delay(1, 2)

        try:
            # Search for clickable element containing the symbol inside iframe
            # Try multiple selector strategies
            button = None

            # Strategy 1: Exact text match
            try:
                button = iframe.locator(f"text={askslim_symbol}").first
                button.wait_for(state="visible", timeout=5000)
            except:
                pass

            # Strategy 2: Button or link containing text
            if not button:
                try:
                    button = iframe.locator(f"button:has-text('{askslim_symbol}'), a:has-text('{askslim_symbol}')").first
                    button.wait_for(state="visible", timeout=5000)
                except:
                    pass

            # Strategy 3: Any clickable element
            if not button:
                button = iframe.locator(f"[role='button']:has-text('{askslim_symbol}'), div[onclick]:has-text('{askslim_symbol}')").first
                button.wait_for(state="visible", timeout=5000)

            button.click()
            print(f"✓ Clicked {askslim_symbol}")
        except Exception as e:
            print(f"✗ Could not find/click button for {askslim_symbol}: {e}")
            return None

        # Wait for modal to appear (check both main page and iframe)
        human_delay(1.5, 2.5)

        modal_context = None
        try:
            page.wait_for_selector("text=Technical Overview", timeout=5000)
            modal_context = page
            print("✓ Modal opened in main page")
        except:
            try:
                iframe.wait_for_selector("text=Technical Overview", timeout=5000)
                modal_context = iframe
                print("✓ Modal opened in iframe")
            except:
                print("✗ Could not find modal")
                return None

        # Click TECHNICAL DETAILS tab
        human_delay(0.5, 1)
        tech_tab = modal_context.wait_for_selector("text=TECHNICAL DETAILS", timeout=5000)
        tech_tab.click()
        print("✓ Switched to TECHNICAL DETAILS")

        human_delay(1, 2)

        # Expand "Cycle Low Dates"
        cycle_dates_section = modal_context.wait_for_selector("text=Cycle Low Dates", timeout=5000)
        cycle_dates_section.click()
        print("✓ Expanded Cycle Low Dates")

        human_delay(0.5, 1)

        # Extract cycle dates using CSS classes
        weekly_date = None
        daily_date = None

        # Find all cycle detail columns
        columns = modal_context.query_selector_all(".cycle-detail_column__sJ7wK, [class*='cycle-detail_column']")

        for column in columns:
            # Get the full text content of the column
            column_text = column.text_content()

            if not column_text:
                continue

            # Check if this is the Weekly or Daily column
            if "Weekly" in column_text:
                # Extract date from text (it's usually right after "Weekly")
                import re
                match = re.search(r'(\d{2}/\d{2}/\d{2})', column_text)
                if match:
                    weekly_date = parse_askslim_date(match.group(1))

            elif "Daily" in column_text:
                # Extract date from text
                import re
                match = re.search(r'(\d{2}/\d{2}/\d{2})', column_text)
                if match:
                    daily_date = parse_askslim_date(match.group(1))

        print(f"  Weekly date: {weekly_date}")
        print(f"  Daily date: {daily_date}")

        # Collapse Cycle Low Dates
        cycle_dates_section.click()
        human_delay(0.5, 1)

        # Expand "Cycle Counts"
        cycle_counts_section = modal_context.wait_for_selector("text=Cycle Counts", timeout=5000)
        cycle_counts_section.click()
        print("✓ Expanded Cycle Counts")

        human_delay(0.5, 1)

        # Extract cycle lengths using CSS classes
        weekly_length = None
        daily_length = None

        # Find all bar count entries
        bar_entries = modal_context.query_selector_all(".technical-briefing_barCountEntry__Kjp0h, [class*='barCountEntry']")

        for entry in bar_entries:
            entry_text = entry.text_content()

            if not entry_text:
                continue

            # Check if this is Weekly or Daily dominant cycle
            if "Weekly Dominant Cycle" in entry_text:
                # Extract "37 bars" from text
                import re
                match = re.search(r'(\d+)\s+bars?', entry_text)
                if match:
                    weekly_length = int(match.group(1))

            elif "Daily Dominant Cycle" in entry_text:
                # Extract "26 bars" from text
                import re
                match = re.search(r'(\d+)\s+bars?', entry_text)
                if match:
                    daily_length = int(match.group(1))

        print(f"  Weekly length: {weekly_length} bars")
        print(f"  Daily length: {daily_length} bars")

        # Collapse Cycle Counts
        cycle_counts_section.click()
        human_delay(0.5, 1)

        # Extract Directional Bias
        directional_bias = None
        try:
            # Find the Directional Bias accordion summary
            bias_elements = modal_context.query_selector_all("text=/Directional Bias/i")
            for elem in bias_elements:
                try:
                    # Get the parent accordion summary which contains both label and value
                    parent_text = elem.evaluate("el => el.parentElement ? el.parentElement.textContent : null")
                    if parent_text:
                        # Extract bias (Bullish, Bearish, or Neutral)
                        for bias in ['Bullish', 'Bearish', 'Neutral']:
                            if bias in parent_text:
                                directional_bias = bias
                                break
                        if directional_bias:
                            break
                except:
                    continue
            print(f"  Directional Bias: {directional_bias}")
        except Exception as e:
            print(f"  ⚠ Could not extract directional bias: {e}")

        # Extract Weekly Key Levels
        weekly_support = None
        weekly_resistance = None
        try:
            weekly_levels_section = modal_context.wait_for_selector("text=Weekly Key Levels", timeout=5000)
            weekly_levels_section.click()
            print("✓ Expanded Weekly Key Levels")
            human_delay(0.5, 1)

            # Get the expanded accordion content
            expanded_content = modal_context.query_selector(".MuiAccordion-root.Mui-expanded .MuiAccordionDetails-root")
            if expanded_content:
                levels_text = expanded_content.text_content()
                import re

                # Find support level
                support_match = re.search(r'Cycle Low Support\s*([0-9.,]+)', levels_text)
                if support_match:
                    weekly_support = float(support_match.group(1).replace(',', ''))

                # Find resistance level - handle both numeric and text values
                resistance_match = re.search(r'Cycle Peak Resistance\s*([0-9.,]+)', levels_text)
                if resistance_match:
                    weekly_resistance = float(resistance_match.group(1).replace(',', ''))

            print(f"  Weekly Support: {weekly_support}, Resistance: {weekly_resistance}")

            # Collapse section
            weekly_levels_section.click()
            human_delay(0.5, 1)
        except Exception as e:
            print(f"  ⚠ Could not extract weekly key levels: {e}")

        # Extract Daily Key Levels
        daily_support = None
        daily_resistance = None
        try:
            daily_levels_section = modal_context.wait_for_selector("text=Daily Key Levels", timeout=5000)
            daily_levels_section.click()
            print("✓ Expanded Daily Key Levels")
            human_delay(0.5, 1)

            # Get the expanded accordion content
            expanded_content = modal_context.query_selector(".MuiAccordion-root.Mui-expanded .MuiAccordionDetails-root")
            if expanded_content:
                levels_text = expanded_content.text_content()
                import re

                # Find support level
                support_match = re.search(r'Cycle Low Support\s*([0-9.,]+)', levels_text)
                if support_match:
                    daily_support = float(support_match.group(1).replace(',', ''))

                # Find resistance level
                resistance_match = re.search(r'Cycle Peak Resistance\s*([0-9.,]+)', levels_text)
                if resistance_match:
                    daily_resistance = float(resistance_match.group(1).replace(',', ''))

            print(f"  Daily Support: {daily_support}, Resistance: {daily_resistance}")

            # Collapse section
            daily_levels_section.click()
            human_delay(0.5, 1)
        except Exception as e:
            print(f"  ⚠ Could not extract daily key levels: {e}")

        # Extract Video Analysis URL
        video_url = None
        try:
            # Click on VIDEO ANALYSIS tab
            video_tab = modal_context.wait_for_selector("text=Video Analysis", timeout=5000)
            video_tab.click()
            print("✓ Switched to Video Analysis")
            human_delay(1, 2)

            # Look for YouTube iframe or link
            iframe_elem = modal_context.query_selector("iframe[src*='youtube']")
            if iframe_elem:
                video_url = iframe_elem.get_attribute("src")
                # Convert embed URL to watch URL
                if '/embed/' in video_url:
                    video_id = video_url.split('/embed/')[-1].split('?')[0]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"

            print(f"  Video URL: {video_url}")

            # Switch back to TECHNICAL DETAILS
            tech_tab = modal_context.wait_for_selector("text=TECHNICAL DETAILS", timeout=5000)
            tech_tab.click()
            human_delay(0.5, 1)
        except Exception as e:
            print(f"  ⚠ Could not extract video URL: {e}")

        # Switch to WEEKLY CHART tab to download chart
        weekly_tab = modal_context.wait_for_selector("text=WEEKLY CHART", timeout=5000)
        weekly_tab.click()
        print("✓ Switched to WEEKLY CHART")

        human_delay(1.5, 2)
        download_chart(modal_context, page, riley_symbol, "WEEKLY")

        # Switch to DAILY CHART tab
        daily_tab = modal_context.wait_for_selector("text=DAILY CHART", timeout=5000)
        daily_tab.click()
        print("✓ Switched to DAILY CHART")

        human_delay(1.5, 2)
        download_chart(modal_context, page, riley_symbol, "DAILY")

        # Update database with cycle specs and key levels
        if weekly_date and weekly_length:
            update_riley_database(riley_symbol, "W", weekly_date, weekly_length,
                                support_level=weekly_support,
                                resistance_level=weekly_resistance)

        if daily_date and daily_length:
            update_riley_database(riley_symbol, "D", daily_date, daily_length,
                                support_level=daily_support,
                                resistance_level=daily_resistance)

        # Update instrument analysis (directional bias and video URL)
        if directional_bias or video_url:
            update_instrument_analysis(riley_symbol, directional_bias, video_url)

        # Close modal - CRITICAL to close before next instrument
        human_delay(0.5, 1)

        # Try multiple strategies to close the modal
        closed = False

        # Strategy 1: Find close button by SVG icon (Cancel/X icon)
        try:
            close_btn = modal_context.query_selector("button:has(svg[data-testid='CancelIcon'])")
            if close_btn:
                close_btn.click()
                closed = True
                print("✓ Closed modal (CancelIcon)")
        except:
            pass

        # Strategy 2: Find any button in modal header
        if not closed:
            try:
                close_btn = modal_context.query_selector(".modal-header button")
                if close_btn:
                    close_btn.click()
                    closed = True
                    print("✓ Closed modal (header button)")
            except:
                pass

        # Strategy 3: Press Escape key
        if not closed:
            try:
                modal_context.keyboard.press("Escape")
                closed = True
                print("✓ Closed modal (Escape key)")
            except:
                pass

        if not closed:
            print("  ⚠ Could not close modal - may affect next instrument")

        human_delay(1, 2)

        return {
            "askslim_symbol": askslim_symbol,
            "riley_symbol": riley_symbol,
            "weekly_date": weekly_date,
            "daily_date": daily_date,
            "weekly_length": weekly_length,
            "daily_length": daily_length
        }

    except Exception as e:
        print(f"✗ Error scraping {askslim_symbol}: {e}")
        import traceback
        traceback.print_exc()

        # Try to close modal if open
        try:
            # Try both contexts
            for context in [page, iframe]:
                close_button = (
                    context.query_selector("button[aria-label='Close']") or
                    context.query_selector(".close") or
                    context.query_selector("button:has-text('×')") or
                    context.query_selector("button:has-text('Close')")
                )
                if close_button:
                    close_button.click()
                    break
        except:
            pass

        return None


def run_scraper(headless=True):
    """
    Run the complete scraper.

    Args:
        headless: Run browser in headless mode (default True for automation)
    """
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first")
        return False

    print("="*70)
    print("askSlim Complete Scraper - Phase 2")
    print("="*70)
    print(f"Database: {DB_PATH}")
    print(f"Media folder: {MEDIA_PATH}")
    print(f"Instruments to scrape: {len(ASKSLIM_TO_RILEY)}")
    print(f"Headless mode: {headless}")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=200)
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            # Navigate to Futures Hub
            print("\nNavigating to Futures Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/futures-hub/", wait_until="networkidle")

            # Wait for page to fully load (JavaScript rendering)
            print("Waiting for page to load...")
            human_delay(3, 5)

            # Find the futures hub iframe
            print("Looking for futures hub iframe...")
            iframe_element = page.wait_for_selector("iframe.fuhub-frame", timeout=15000)
            print("✓ Found iframe")

            # Get the iframe's content frame
            iframe = iframe_element.content_frame()
            print("✓ Got iframe content")

            # Wait for instruments to load inside iframe
            print("Waiting for instruments to load in iframe...")
            human_delay(3, 5)

            # Wait for SPX to be visible inside iframe
            print("Waiting for SPX to appear...")
            iframe.wait_for_selector("text=SPX", timeout=15000)
            print("✓ Instruments loaded")

            results = []

            # Scrape each instrument
            for askslim_symbol in ASKSLIM_TO_RILEY.keys():
                result = scrape_instrument(page, askslim_symbol, iframe)
                if result:
                    results.append(result)

                # Random delay between instruments (4-8 seconds to avoid bot detection)
                human_delay(4, 8)

            # Summary
            print("\n" + "="*70)
            print("SCRAPING COMPLETE")
            print("="*70)
            print(f"Instruments scraped: {len(results)}/{len(ASKSLIM_TO_RILEY)}")
            print(f"Database updated: {DB_PATH}")
            print(f"Charts saved to: {MEDIA_PATH}")
            print("="*70)

            return True

        except Exception as e:
            print(f"\nFATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    try:
        success = run_scraper()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        sys.exit(1)
