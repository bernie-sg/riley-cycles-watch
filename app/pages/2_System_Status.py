"""
System Status and Admin Page
Shows component status with clear sections
"""
import streamlit as st
import sqlite3
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
import pandas as pd

# Page config
st.set_page_config(
    page_title="System Status - Riley Cycles Watch",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ System Status & Admin")

# Get project root
project_root = Path(__file__).parent.parent.parent

# Database path
db_path = project_root / "db" / "riley.sqlite"

# Logs directory
logs_dir = project_root / "logs"
logs_dir.mkdir(exist_ok=True)


def get_file_status(filepath):
    """Get file modification time and size"""
    if filepath.exists():
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        size = filepath.stat().st_size
        return {'exists': True, 'modified': mtime, 'size': size}
    else:
        return {'exists': False, 'modified': None, 'size': 0}


def get_db_stats():
    """Get database statistics"""
    conn = sqlite3.connect(db_path)
    stats = {}

    try:
        # Total instruments
        cursor = conn.execute("SELECT COUNT(*) FROM instruments WHERE role = 'CANONICAL'")
        stats['total_instruments'] = cursor.fetchone()[0]

        # Active cycle specs
        cursor = conn.execute("SELECT COUNT(*) FROM cycle_specs WHERE status = 'ACTIVE'")
        stats['active_cycle_specs'] = cursor.fetchone()[0]

        # Price bars
        cursor = conn.execute("SELECT COUNT(*), MIN(date), MAX(date) FROM price_bars_daily")
        row = cursor.fetchone()
        stats['price_bars'] = {
            'count': row[0],
            'min_date': row[1],
            'max_date': row[2]
        }

        # Trading calendar
        cursor = conn.execute("SELECT instrument_id FROM instruments WHERE symbol = 'ES' AND role = 'CANONICAL'")
        es_result = cursor.fetchone()
        if es_result:
            es_id = es_result[0]
            cursor = conn.execute("""
                SELECT COUNT(*), MIN(trading_date_label), MAX(trading_date_label)
                FROM trading_calendar_daily
                WHERE instrument_id = ?
            """, (es_id,))
            row = cursor.fetchone()
            stats['trading_calendar'] = {
                'count': row[0],
                'min_date': row[1],
                'max_date': row[2]
            }
        else:
            stats['trading_calendar'] = {'count': 0, 'min_date': None, 'max_date': None}

        # Last cycle scan
        cursor = conn.execute("""
            SELECT scan_td_label, created_at
            FROM daily_scan_runs
            ORDER BY created_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            stats['last_cycle_scan'] = {
                'label': row[0],
                'timestamp': row[1]
            }
        else:
            stats['last_cycle_scan'] = None

        # Last askSlim scraper run (from instrument_analysis updates)
        cursor = conn.execute("""
            SELECT MAX(updated_at) as last_update, COUNT(*) as instruments_updated
            FROM instrument_analysis
            WHERE status = 'ACTIVE'
        """)
        row = cursor.fetchone()
        if row and row[0]:
            stats['last_scraper_run'] = {
                'timestamp': row[0],
                'instruments': row[1]
            }
        else:
            stats['last_scraper_run'] = None

    finally:
        conn.close()

    return stats


# ============================================================================
# SECTION 1: askSlim Scraper
# ============================================================================
st.header("📡 askSlim Scraper")
st.caption("Extracts cycle data from askSlim.com")

col1, col2 = st.columns([2, 1])

with col1:
    try:
        stats = get_db_stats()

        # Last scraper run
        if stats['last_scraper_run']:
            last_run = pd.to_datetime(stats['last_scraper_run']['timestamp'])
            st.metric(
                "Last Run",
                last_run.strftime('%d-%b-%Y %H:%M:%S'),
                delta=f"{stats['last_scraper_run']['instruments']} instruments updated"
            )
        else:
            st.warning("Scraper has never run")

        # Log file status
        log_file = logs_dir / "askslim_daily.log"
        log_status = get_file_status(log_file)

        if log_status['exists']:
            st.caption(f"Log file: {log_status['size']:,} bytes, modified {log_status['modified'].strftime('%d-%b-%Y %H:%M:%S')}")
        else:
            st.caption("No log file yet (will be created when scraper runs)")

    except Exception as e:
        st.error(f"Error loading scraper status: {e}")

with col2:
    st.subheader("Manual Controls")

    if st.button("🔑 Login to askSlim", use_container_width=True):
        with st.spinner("Logging in (may take up to 2 minutes)..."):
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = str(project_root)

                result = subprocess.run(
                    [sys.executable, str(project_root / "src/riley/modules/askslim/askslim_login.py")],
                    cwd=str(project_root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    st.success("✅ Login successful - session saved")
                else:
                    st.warning("⚠️ Login completed with issues")

                output = result.stdout + ("\n" + result.stderr if result.stderr else "")
                if output.strip():
                    with st.expander("📄 View Output", expanded=False):
                        st.code(output, language="text")
            except subprocess.TimeoutExpired:
                st.error("❌ Login timed out (>5 minutes)")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if st.button("✓ Verify Session", use_container_width=True):
        with st.spinner("Verifying session..."):
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = str(project_root)

                result = subprocess.run(
                    [sys.executable, str(project_root / "src/riley/modules/askslim/askslim_smoketest.py")],
                    cwd=str(project_root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if result.returncode == 0:
                    st.success("✅ Session is valid")
                else:
                    st.warning("⚠️ Session invalid or expired")

                output = result.stdout + ("\n" + result.stderr if result.stderr else "")
                if output.strip():
                    with st.expander("📄 View Output", expanded=False):
                        st.code(output, language="text")
            except subprocess.TimeoutExpired:
                st.error("❌ Verification timed out (>2 minutes)")
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if st.button("▶️ Run Scraper Now", use_container_width=True, type="primary"):
        with st.spinner("Running askSlim scraper (may take up to 1 hour)..."):
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = str(project_root)

                result = subprocess.run(
                    [sys.executable, str(project_root / "src/riley/modules/askslim/askslim_run_daily.py")],
                    cwd=str(project_root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=3600
                )
                if result.returncode == 0:
                    st.success("✅ Scraper completed successfully")
                    st.rerun()  # Refresh to show updated stats
                else:
                    st.warning("⚠️ Scraper completed with issues")

                output = result.stdout + ("\n" + result.stderr if result.stderr else "")
                if output.strip():
                    with st.expander("📄 View Output", expanded=True):
                        st.code(output, language="text")
            except subprocess.TimeoutExpired:
                st.error("❌ Scraper timed out (>60 minutes)")
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.divider()

# ============================================================================
# SECTION 2: Market Data (Price History)
# ============================================================================
st.header("📈 Market Data (Price History)")
st.caption("Daily price bars from Yahoo Finance")

col1, col2 = st.columns([2, 1])

with col1:
    try:
        stats = get_db_stats()

        # Price bars stats
        if stats['price_bars']['max_date']:
            latest = pd.to_datetime(stats['price_bars']['max_date'])
            st.metric(
                "Last Update",
                latest.strftime('%d-%b-%Y'),
                delta=f"{stats['price_bars']['count']:,} total bars"
            )

            if stats['price_bars']['min_date']:
                min_date = pd.to_datetime(stats['price_bars']['min_date']).strftime('%d-%b-%Y')
                max_date = pd.to_datetime(stats['price_bars']['max_date']).strftime('%d-%b-%Y')
                st.caption(f"Date range: {min_date} to {max_date}")
        else:
            st.warning("No price data in database")

        # Log file status
        log_file = logs_dir / "marketdata_cron.log"
        log_status = get_file_status(log_file)

        if log_status['exists']:
            st.caption(f"Log file: {log_status['size']:,} bytes, modified {log_status['modified'].strftime('%d-%b-%Y %H:%M:%S')}")
        else:
            st.caption("No log file yet (will be created when market data updates)")

    except Exception as e:
        st.error(f"Error loading market data status: {e}")

with col2:
    st.subheader("Manual Controls")

    if st.button("🔄 Update Market Data", use_container_width=True, type="primary"):
        with st.spinner("Updating market data (may take 2-5 minutes)..."):
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = str(project_root)

                # Export path for RRG
                export_path = project_root / "artifacts" / "rrg" / "rrg_prices_daily.csv"
                export_path.parent.mkdir(parents=True, exist_ok=True)

                result = subprocess.run(
                    [sys.executable, str(project_root / "scripts/riley_marketdata.py"),
                     "update", "--export", str(export_path)],
                    cwd=str(project_root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300
                )

                if result.returncode == 0:
                    st.success("✅ Market data updated")
                    st.rerun()  # Refresh to show updated stats
                else:
                    st.warning("⚠️ Update completed with issues")

                output = result.stdout + ("\n" + result.stderr if result.stderr else "")
                if output.strip():
                    with st.expander("📄 View Output", expanded=True):
                        st.code(output, language="text")
            except subprocess.TimeoutExpired:
                st.error("❌ Update timed out (>5 minutes)")
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.divider()

# ============================================================================
# SECTION 3: Cycle Scanner
# ============================================================================
st.header("🔍 Cycle Scanner")
st.caption("Analyzes cycle windows and generates priority lists")

col1, col2 = st.columns([2, 1])

with col1:
    try:
        stats = get_db_stats()

        # Last cycle scan
        if stats['last_cycle_scan']:
            scan_label = stats['last_cycle_scan']['label']
            scan_time = pd.to_datetime(stats['last_cycle_scan']['timestamp'])

            st.metric(
                "Last Scan",
                scan_label,
                delta=scan_time.strftime('%d-%b-%Y %H:%M:%S')
            )
        else:
            st.warning("Cycle scanner has never run")

        # Recent scans table
        st.subheader("Recent Scans")
        conn = sqlite3.connect(db_path)
        df_scans = pd.read_sql_query("""
            SELECT
                dsr.scan_td_label as "Scan Date",
                dsr.created_at as "Run At",
                COUNT(*) as "Total Instruments",
                SUM(CASE WHEN dsr2.daily_status = 'IN_WINDOW' OR dsr2.weekly_status = 'IN_WINDOW' THEN 1 ELSE 0 END) as "In Window"
            FROM daily_scan_runs dsr
            LEFT JOIN daily_scan_rows dsr2 ON dsr.scan_id = dsr2.scan_id
            GROUP BY dsr.scan_id, dsr.scan_td_label, dsr.created_at
            ORDER BY dsr.created_at DESC
            LIMIT 10
        """, conn)
        conn.close()

        if not df_scans.empty:
            # Format timestamps
            df_scans['Run At'] = pd.to_datetime(df_scans['Run At']).dt.strftime('%d-%b-%Y %H:%M:%S')
            st.dataframe(df_scans, use_container_width=True, hide_index=True)
        else:
            st.info("No scans found")

    except Exception as e:
        st.error(f"Error loading cycle scanner status: {e}")

with col2:
    st.subheader("Manual Controls")

    if st.button("▶️ Run Cycle Scanner", use_container_width=True, type="primary"):
        with st.spinner("Running cycle scanner..."):
            try:
                env = os.environ.copy()
                env['PYTHONPATH'] = str(project_root)

                # Get today's date
                from datetime import datetime
                asof_date = datetime.now().strftime('%Y-%m-%d')

                result = subprocess.run(
                    [sys.executable, str(project_root / "scripts/cycles_run_scan.py"), "--asof", asof_date],
                    cwd=str(project_root),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode == 0:
                    st.success("✅ Cycle scan completed")
                    st.rerun()  # Refresh to show updated stats
                else:
                    st.warning("⚠️ Scan completed with issues")

                output = result.stdout + ("\n" + result.stderr if result.stderr else "")
                if output.strip():
                    with st.expander("📄 View Output", expanded=True):
                        st.code(output, language="text")
            except subprocess.TimeoutExpired:
                st.error("❌ Scan timed out (>1 minute)")
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.divider()

# ============================================================================
# SECTION 4: Database Overview
# ============================================================================
st.header("💾 Database Overview")

try:
    stats = get_db_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Instruments", stats['total_instruments'])

    with col2:
        st.metric("Active Cycle Specs", stats['active_cycle_specs'])

    with col3:
        st.metric("Price Bars", f"{stats['price_bars']['count']:,}")

    with col4:
        st.metric("Trading Days (ES)", f"{stats['trading_calendar']['count']:,}")

except Exception as e:
    st.error(f"Error loading database overview: {e}")

st.divider()

# ============================================================================
# SECTION 5: Log Viewers
# ============================================================================
st.header("📋 Log Files")

tab1, tab2 = st.tabs(["askSlim Log", "Market Data Log"])

with tab1:
    log_file = logs_dir / "askslim_daily.log"
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                log_content = f.read()
            st.code(log_content, language="text")
        except Exception as e:
            st.error(f"Error reading log: {e}")
    else:
        st.info("Log file will be created when askSlim scraper runs on server")

with tab2:
    log_file = logs_dir / "marketdata_cron.log"
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                log_content = f.read()
            st.code(log_content, language="text")
        except Exception as e:
            st.error(f"Error reading log: {e}")
    else:
        st.info("Log file will be created when market data update runs")
