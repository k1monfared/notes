#!/bin/bash
cd "$(dirname "$0")/backend"

echo "Installing backend dependencies..."
python3 -m pip install -r requirements.txt

echo ""
echo "Starting backend on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

python3 main.py
