@echo off
REM Quick start script for Sector Rotation Map (Windows)

echo Starting Sector Rotation Map...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Run Streamlit app
echo Launching app...
echo.
streamlit run app.py

pause
