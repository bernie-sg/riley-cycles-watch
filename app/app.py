"""
Compatibility entrypoint (legacy)

Streamlit now uses app/Home.py for multipage format.
This file exists to avoid "missing app.py" errors from old commands.

If you're running:
  streamlit run app/app.py

It will automatically forward to Home.py.

Recommended: Use `streamlit run app/Home.py` or `bash scripts/run_ui.sh`
"""

import sys
from pathlib import Path
import runpy

# Add app directory to sys.path for absolute imports (config, db, etc.)
APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

# Forward to the actual entrypoint
home = Path(__file__).with_name("Home.py")
runpy.run_path(str(home), run_name="__main__")
