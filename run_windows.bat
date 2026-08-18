@echo off
title AI Question Extractor & Automator

echo ============================================================
echo     AI Question Extractor & Automator Setup & Runner
echo ============================================================
echo.

:: Step 1: Check Python installation
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not found on this Windows system.
    echo [*] Attempting to install Python automatically via winget...
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo [*] Downloading official Python installer...
        curl -o python_setup.exe https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
        start /wait python_setup.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        del python_setup.exe
    )
    echo [OK] Python installed successfully.
)

for /f "tokens=*" %%i in ('python --version') do echo [OK] Found %%i
echo.

:: Step 2: Initialize virtual environment
echo [2/4] Setting up isolated Python virtual environment (.venv)...
if not exist .venv (
    python -m venv .venv
    echo [OK] Created new virtual environment in .venv
) else (
    echo [OK] Existing .venv directory found.
)

call .venv\Scripts\activate
echo [OK] Virtual environment activated.
echo.

:: Step 3: Install dependencies
echo [3/4] Checking and installing required packages...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt
echo [OK] All dependencies are ready.
echo.

:: Step 4: Run Streamlit application
echo [4/4] Starting Web Dashboard...

:: Silence Streamlit onboarding email prompt permanently
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    echo [general] > "%USERPROFILE%\.streamlit\credentials.toml"
    echo email = "" >> "%USERPROFILE%\.streamlit\credentials.toml"
)

echo [*] Opening browser at http://localhost:8501
echo ============================================================
echo  Close this window to stop the application.
echo ============================================================
echo.

streamlit run app.py --browser.gatherUsageStats=false

pause
