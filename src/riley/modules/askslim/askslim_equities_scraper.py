#!/usr/bin/env python3
"""
askSlim Equities/ETFs Hub Scraper
Scrapes equity and ETF instruments for cycle data and charts.
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

# Import shared functions from main scraper
sys.path.insert(0, str(Path(__file__).parent))
from askslim_scraper import (
    human_delay, parse_askslim_date, parse_cycle_bars,
    update_instrument_analysis, update_riley_database,
    download_chart, DB_PATH, MEDIA_PATH, PROJECT_ROOT
)

# Load environment variables
load_dotenv()

ASKSLIM_BASE_URL = os.getenv("ASKSLIM_BASE_URL", "https://askslim.com")
ASKSLIM_HEADLESS = os.getenv("ASKSLIM_HEADLESS", "true").lower() == "true"

DEFAULT_STORAGE_STATE_PATH = Path(__file__).parent / "storage_state.json"
ASKSLIM_STORAGE_STATE_PATH = os.getenv("ASKSLIM_STORAGE_STATE_PATH", str(DEFAULT_STORAGE_STATE_PATH))

# Equities & ETFs mapping: askSlim symbol -> Riley canonical symbol
# For most equities/ETFs, we use the same symbol
ASKSLIM_EQUITIES_TO_RILEY = {
    # Indexes (map to futures)
    "SPX": "ES",   # S&P 500 Index → ES futures
    "NDX": "NQ",   # NASDAQ-100 Index → NQ futures
    "RUT": "RTY",  # Russell 2000 Index → RTY futures

    # Individual Stocks - use same symbol
    "AAPL": "AAPL",
    "AMAT": "AMAT",
    "AMD": "AMD",
    "AMGN": "AMGN",
    "AMZN": "AMZN",
    "AVGO": "AVGO",
    "BA": "BA",
    "BABA": "BABA",
    "BIDU": "BIDU",
    "CAT": "CAT",
    "COST": "COST",
    "CRM": "CRM",
    "CVX": "CVX",
    "DE": "DE",
    "DIS": "DIS",
    "FCX": "FCX",
    "FDX": "FDX",
    "FSLR": "FSLR",
    "GOOGL": "GOOGL",
    "GS": "GS",
    "HD": "HD",
    "JPM": "JPM",
    "LUV": "LUV",
    "LVS": "LVS",
    "MCD": "MCD",
    "META": "META",
    "MS": "MS",
    "MSFT": "MSFT",
    "MU": "MU",
    "NEM": "NEM",
    "NFLX": "NFLX",
    "NKE": "NKE",
    "NVDA": "NVDA",
    "ORCL": "ORCL",
    "PAAS": "PAAS",
    "PEP": "PEP",
    "PYPL": "PYPL",
    "SBUX": "SBUX",
    "TMUS": "TMUS",
    "TOL": "TOL",
    "TSLA": "TSLA",
    "UAL": "UAL",
    "UBER": "UBER",
    "V": "V",
    "WMT": "WMT",
    "WYNN": "WYNN",
    "XOM": "XOM",

    # ETFs - use same symbol
    "SMH": "SMH",
    "XBI": "XBI",
    "XLE": "XLE",
    "XLF": "XLF",
    "XLI": "XLI",
    "XLK": "XLK",
    "XLP": "XLP",
    "XRT": "XRT",
    "EEM": "EEM",
    "FEZ": "FEZ",
    "FXI": "FXI",
    "GDX": "GDX",
}

# Skip VIX and any other instruments as requested
SKIP_EQUITIES = {"VIX", "XYZ"}  # XYZ appears to be placeholder/error


def scrape_equity_instrument(page, askslim_symbol, iframe):
    """
    Scrape a single equity/ETF instrument from the Equities/ETFs Hub.

    Args:
        page: Playwright page object (main page)
        askslim_symbol: Symbol as shown in askSlim (e.g., "AAPL")
        iframe: Content frame of the eehub iframe

    Returns:
        dict with scraped data, or None if failed
    """
    if askslim_symbol in SKIP_EQUITIES:
        print(f"\n⏭ Skipping {askslim_symbol} (in skip list)")
        return None

    riley_symbol = ASKSLIM_EQUITIES_TO_RILEY.get(askslim_symbol)
    if not riley_symbol:
        print(f"\n⚠ No mapping for {askslim_symbol}, skipping")
        return None

    print("\n" + "="*60)
    print(f"Scraping: {askslim_symbol} → {riley_symbol}")
    print("="*60)

    try:
        # Click on the instrument (handle off-screen elements)
        # Use a more specific selector that targets visible ticker, not hidden full-name
        instrument_selector = f"div:not(.full-name):has-text('{askslim_symbol}')"

        # Wait for element to be attached (not necessarily visible)
        instrument_elem = iframe.wait_for_selector(instrument_selector, state='attached', timeout=10000)

        # Try to scroll parent container to make element visible
        try:
            # Get the parent grid container and scroll it
            iframe.evaluate("""
                (selector) => {
                    const element = document.evaluate(
                        `//*[contains(text(), '${selector}')]`,
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    ).singleNodeValue;
                    if (element) {
                        // Find scrollable parent
                        let parent = element.parentElement;
                        while (parent) {
                            const overflow = window.getComputedStyle(parent).overflow;
                            if (overflow === 'auto' || overflow === 'scroll' || overflow === 'hidden') {
                                parent.scrollTop = element.offsetTop - parent.offsetTop;
                                break;
                            }
                            parent = parent.parentElement;
                        }
                        // Also try scrollIntoView
                        element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    }
                }
            """, askslim_symbol)
            human_delay(1, 2)  # Wait for scroll animation
        except:
            pass

        # Force click even if not visible
        instrument_elem.click(force=True)
        print(f"✓ Clicked {askslim_symbol}")
        human_delay(1, 2)

        # Wait for modal to open
        modal_context = iframe.wait_for_selector("[class*='Modal']", timeout=5000)
        print("✓ Modal opened in iframe")
        human_delay(0.5, 1)

        # Switch to Technical Details tab (it's the LAST tab in Equities Hub)
        tech_details_tab = iframe.wait_for_selector("text=Technical Details", timeout=5000)
        tech_details_tab.click()
        print("✓ Switched to Technical Details")
        human_delay(1, 2)

        # Extract Directional Bias
        directional_bias = None
        try:
            bias_elements = modal_context.query_selector_all("text=/Directional Bias/i")
            for elem in bias_elements:
                parent_text = elem.evaluate("el => el.parentElement ? el.parentElement.textContent : null")
                if parent_text:
                    for bias in ['Bullish', 'Bearish', 'Neutral']:
                        if bias in parent_text:
                            directional_bias = bias
                            break
                if directional_bias:
                    break
            print(f"  Directional Bias: {directional_bias}")
        except Exception as e:
            print(f"  ⚠ Could not extract directional bias: {e}")

        # Expand Cycle Low Dates
        cycle_dates_section = modal_context.wait_for_selector("text=Cycle Low Dates", timeout=5000)
        cycle_dates_section.click()
        print("✓ Expanded Cycle Low Dates")
        human_delay(0.5, 1)

        # Extract cycle dates
        expanded_content = modal_context.query_selector(".MuiAccordion-root.Mui-expanded .MuiAccordionDetails-root")
        dates_text = expanded_content.text_content() if expanded_content else ""

        # Parse Weekly date
        weekly_date = None
        import re
        weekly_match = re.search(r'Weekly\s*(\d{2}/\d{2}/\d{2})', dates_text)
        if weekly_match:
            weekly_date = parse_askslim_date(weekly_match.group(1))

        # Parse Daily date
        daily_date = None
        daily_match = re.search(r'Daily\s*(\d{2}/\d{2}/\d{2})', dates_text)
        if daily_match:
            daily_date = parse_askslim_date(daily_match.group(1))

        print(f"  Weekly date: {weekly_date}")
        print(f"  Daily date: {daily_date}")

        # Collapse Cycle Low Dates
        cycle_dates_section.click()
        human_delay(0.3, 0.5)

        # Expand Cycle Counts
        cycle_counts_section = modal_context.wait_for_selector("text=Cycle Counts", timeout=5000)
        cycle_counts_section.click()
        print("✓ Expanded Cycle Counts")
        human_delay(0.5, 1)

        # Extract cycle lengths
        expanded_content = modal_context.query_selector(".MuiAccordion-root.Mui-expanded .MuiAccordionDetails-root")
        counts_text = expanded_content.text_content() if expanded_content else ""

        weekly_length = None
        weekly_length_match = re.search(r'Weekly Dominant Cycle\s*(\d+)\s*bars?', counts_text)
        if weekly_length_match:
            weekly_length = int(weekly_length_match.group(1))

        daily_length = None
        daily_length_match = re.search(r'Daily Dominant Cycle\s*(\d+)\s*bars?', counts_text)
        if daily_length_match:
            daily_length = int(daily_length_match.group(1))

        print(f"  Weekly length: {weekly_length} bars")
        print(f"  Daily length: {daily_length} bars")

        # Collapse Cycle Counts
        cycle_counts_section.click()
        human_delay(0.3, 0.5)

        # Extract Weekly Key Levels
        weekly_support = None
        weekly_resistance = None
        try:
            weekly_levels_section = modal_context.wait_for_selector("text=Weekly Key Levels", timeout=5000)
            weekly_levels_section.click()
            print("✓ Expanded Weekly Key Levels")
            human_delay(0.5, 1)

            expanded_content = modal_context.query_selector(".MuiAccordion-root.Mui-expanded .MuiAccordionDetails-root")
            if expanded_content:
                levels_text = expanded_content.text_content()

                support_match = re.search(r'Cycle Low Support\s*([0-9.,]+)', levels_text)
                if support_match:
                    weekly_support = float(support_match.group(1).replace(',', ''))

                resistance_match = re.search(r'Cycle Peak Resistance\s*([0-9.,]+)', levels_text)
                if resistance_match:
                    weekly_resistance = float(resistance_match.group(1).replace(',', ''))

            print(f"  Weekly Support: {weekly_support}, Resistance: {weekly_resistance}")
            weekly_levels_section.click()  # Collapse
            human_delay(0.3, 0.5)
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

            expanded_content = modal_context.query_selector(".MuiAccordion-root.Mui-expanded .MuiAccordionDetails-root")
            if expanded_content:
                levels_text = expanded_content.text_content()

                support_match = re.search(r'Cycle Low Support\s*([0-9.,]+)', levels_text)
                if support_match:
                    daily_support = float(support_match.group(1).replace(',', ''))

                resistance_match = re.search(r'Cycle Peak Resistance\s*([0-9.,]+)', levels_text)
                if resistance_match:
                    daily_resistance = float(resistance_match.group(1).replace(',', ''))

            print(f"  Daily Support: {daily_support}, Resistance: {daily_resistance}")
            daily_levels_section.click()  # Collapse
            human_delay(0.3, 0.5)
        except Exception as e:
            print(f"  ⚠ Could not extract daily key levels: {e}")

        # Check if Video Analysis tab exists
        video_url = None
        try:
            video_tab = modal_context.query_selector("text=Video Analysis")
            if video_tab:
                video_tab.click()
                print("✓ Switched to Video Analysis")
                human_delay(1, 2)

                iframe_elem = modal_context.query_selector("iframe[src*='youtube']")
                if iframe_elem:
                    video_url = iframe_elem.get_attribute("src")
                    # Convert embed URL to watch URL
                    if '/embed/' in video_url:
                        video_id = video_url.split('/embed/')[-1].split('?')[0]
                        video_url = f"https://www.youtube.com/watch?v={video_id}"

                print(f"  Video URL: {video_url}")

                # Switch back to Technical Details
                tech_tab = modal_context.wait_for_selector("text=Technical Details", timeout=5000)
                tech_tab.click()
                human_delay(0.5, 1)
        except Exception as e:
            print(f"  ⚠ No Video Analysis tab or could not extract: {e}")

        # Download charts (switch to chart tabs)
        # Weekly Chart
        try:
            weekly_chart_tab = iframe.wait_for_selector("text=Weekly Chart", timeout=5000)
            weekly_chart_tab.click()
            print("✓ Switched to WEEKLY CHART")
            download_chart(modal_context, page, riley_symbol, "WEEKLY")
        except Exception as e:
            print(f"  ⚠ Could not download weekly chart: {e}")

        # Daily Chart
        try:
            daily_chart_tab = iframe.wait_for_selector("text=Daily Chart", timeout=5000)
            daily_chart_tab.click()
            print("✓ Switched to DAILY CHART")
            download_chart(modal_context, page, riley_symbol, "DAILY")
        except Exception as e:
            print(f"  ⚠ Could not download daily chart: {e}")

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

        # Close modal
        try:
            close_button = modal_context.query_selector("[data-testid='CancelIcon']")
            if close_button:
                close_button.click()
                print("✓ Closed modal (CancelIcon)")
        except:
            # Try ESC key
            iframe.press("body", "Escape")
            print("✓ Closed modal (ESC)")

        human_delay(1, 2)

        return {
            "askslim_symbol": askslim_symbol,
            "riley_symbol": riley_symbol,
            "weekly_date": weekly_date,
            "weekly_length": weekly_length,
            "daily_date": daily_date,
            "daily_length": daily_length,
            "directional_bias": directional_bias,
            "video_url": video_url,
        }

    except Exception as e:
        print(f"❌ Error scraping {askslim_symbol}: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_equities_scraper():
    """Run the complete Equities/ETFs Hub scraper."""
    storage_state_path = Path(ASKSLIM_STORAGE_STATE_PATH)

    if not storage_state_path.exists():
        print("ERROR: Run askslim_login.py first to create storage_state.json")
        return False

    print("="*70)
    print("askSlim Equities/ETFs Hub Complete Scraper")
    print("="*70)
    print(f"\nTotal instruments to scrape: {len(ASKSLIM_EQUITIES_TO_RILEY)}")
    print(f"Skipping: {', '.join(SKIP_EQUITIES)}")
    print("="*70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=ASKSLIM_HEADLESS, slow_mo=500)
        context = browser.new_context(
            storage_state=str(storage_state_path),
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        try:
            # Navigate to Equities/ETFs Hub
            print("\n📡 Navigating to Equities/ETFs Hub...")
            page.goto(f"{ASKSLIM_BASE_URL}/equities-and-etfs-hub/", wait_until="networkidle")
            human_delay(2, 3)

            # Find the eehub iframe
            print("🔍 Looking for eehub iframe...")
            iframe_element = page.wait_for_selector("iframe.eehub-frame", timeout=15000)
            print("✓ Found iframe")

            # Get the iframe's content frame
            iframe = iframe_element.content_frame()
            print("✓ Got iframe content")

            # Wait for instruments to load
            print("⏳ Waiting for instruments to load...")
            human_delay(3, 5)

            # Verify instruments are visible
            iframe.wait_for_selector("text=AAPL", timeout=15000)
            print("✓ Instruments loaded")

            # Scrape all instruments
            results = []
            for askslim_symbol in ASKSLIM_EQUITIES_TO_RILEY.keys():
                if askslim_symbol in SKIP_EQUITIES:
                    continue

                result = scrape_equity_instrument(page, askslim_symbol, iframe)
                if result:
                    results.append(result)

                # Random delay between instruments (4-8 seconds to avoid bot detection)
                human_delay(4, 8)

            # Summary
            print("\n" + "="*70)
            print("SCRAPING COMPLETE")
            print("="*70)
            print(f"✅ Successfully scraped: {len(results)}/{len(ASKSLIM_EQUITIES_TO_RILEY) - len(SKIP_EQUITIES)} instruments")

            return True

        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    success = run_equities_scraper()
    sys.exit(0 if success else 1)
