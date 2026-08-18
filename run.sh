#!/bin/bash
set -e

echo "============================================================"
echo "    AI Question Extractor & Automator Setup & Runner"
echo "============================================================"
echo ""

# Step 1: Check Python installation
echo "[1/4] Checking Python 3 installation..."
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 not found on your system."
    echo "[*] Attempting to install Python 3 automatically..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y python3 python3-pip python3-venv
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y python3 python3-pip
    elif command -v brew &> /dev/null; then
        brew install python3
    else
        echo "[ERROR] Could not install Python automatically. Please install Python 3 manually."
        exit 1
    fi
fi
PYTHON_VER=$(python3 --version)
echo "[OK] Found $PYTHON_VER"
echo ""

# Step 2: Initialize virtual environment
echo "[2/4] Setting up isolated Python virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "[OK] Created new virtual environment in .venv"
else
    echo "[OK] Existing .venv directory found."
fi

source .venv/bin/activate
echo "[OK] Virtual environment activated."
echo ""

# Step 3: Install dependencies
echo "[3/4] Checking and installing required packages (Streamlit, PyMuPDF, Gemini, Selenium)..."
python3 -m pip install --upgrade pip --quiet
python3 -m pip install -r requirements.txt
echo "[OK] All dependencies are ready."
echo ""

# Step 4: Run Streamlit application
echo "[4/4] Starting Web Dashboard..."

# Silence Streamlit onboarding email prompt permanently
mkdir -p ~/.streamlit
if [ ! -f ~/.streamlit/credentials.toml ]; then
    printf "[general]\nemail = \"\"\n" > ~/.streamlit/credentials.toml
fi

echo "[*] Opening browser at http://localhost:8501"
echo "============================================================"
echo " Press Ctrl+C in this terminal to stop the server."
echo "============================================================"
echo ""

streamlit run app.py --browser.gatherUsageStats=false
