"""Cycles Detector V14 - Embedded in Riley"""
import streamlit as st
import requests
from pathlib import Path
import subprocess
import os
import signal

st.set_page_config(
    page_title="Cycles Detector - Riley",
    page_icon="📊",
    layout="wide"
)

# Paths
project_root = Path(__file__).parent.parent.parent
cycles_detector_dir = project_root / "cycles-detector"
app_py = cycles_detector_dir / "app.py"

def check_server_running(port=8082):
    """Check if Flask server is running"""
    try:
        response = requests.get(f"http://localhost:{port}", timeout=1)
        return response.status_code == 200
    except:
        return False

def get_server_pid():
    """Get PID of running Flask server"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python3.*cycles-detector.*app.py"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            return int(result.stdout.strip().split('\n')[0])
    except:
        pass
    return None

def start_server():
    """Start Flask server in background"""
    try:
        # Start Flask server as background process
        process = subprocess.Popen(
            ["python3", "app.py"],
            cwd=str(cycles_detector_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return process.pid
    except Exception as e:
        st.error(f"Failed to start server: {e}")
        return None

def stop_server():
    """Stop Flask server"""
    pid = get_server_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            return True
        except:
            return False
    return False

# Check server status
server_running = check_server_running()

# Server controls in sidebar
with st.sidebar:
    st.subheader("Server Control")

    if server_running:
        st.success("✅ Server Running")
        if st.button("🛑 Stop Server", use_container_width=True):
            if stop_server():
                st.success("Server stopped")
                st.rerun()
            else:
                st.error("Failed to stop server")
    else:
        st.warning("⚠️ Server Not Running")
        if st.button("▶️ Start Server", use_container_width=True, type="primary"):
            with st.spinner("Starting Cycles Detector server..."):
                pid = start_server()
                if pid:
                    import time
                    # Wait for server to start
                    for i in range(10):
                        time.sleep(1)
                        if check_server_running():
                            st.success("Server started!")
                            st.rerun()
                            break
                    else:
                        st.error("Server started but not responding")
                else:
                    st.error("Failed to start server")

# Main content
if server_running:
    # Embed Flask app in iframe - full screen
    st.markdown("""
    <style>
        /* Remove default Streamlit padding */
        .main .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        /* Make iframe fill entire viewport */
        iframe {
            width: 100%;
            height: calc(100vh - 100px);
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)

    st.components.v1.iframe("http://localhost:8082", height=2000, scrolling=True)

else:
    # Server not running - show instructions
    st.info("👆 Click 'Start Server' in the sidebar to launch Cycles Detector")

    st.markdown("---")

    st.markdown("""
    ### About Cycles Detector V14

    **Features:**
    - MESA Cycle Detection (John Ehlers)
    - Morlet Wavelet Analysis
    - Bandpass Filtering with sine wave projection
    - Cycle Heatmaps
    - Quality Metrics (Bartels test, component yield)
    - Multi-Algorithm Support

    **Data Source:**
    - Uses shared CSV files in `data/price_history/`
    - Auto-downloads on demand
    - Shares data with RRG

    **Usage:**
    1. Click "Start Server" in the sidebar
    2. Enter any ticker symbol (AAPL, MSFT, SPY, etc.)
    3. Select wavelength range
    4. View cycle projections and heatmaps
    """)

    st.markdown("---")

    with st.expander("🔧 Manual Server Start (Alternative)"):
        st.markdown("""
        If the automatic start doesn't work, run this in a terminal:

        ```bash
        cd /Users/bernie/Documents/AI/Riley\\ Project/cycles-detector
        python3 app.py
        ```

        Then refresh this page.
        """)

st.caption("Cycles Detector V14 | Embedded Flask Application | Shared CSV Data")
