#!/bin/bash

# Can't Stop Game - Easy Startup Script

echo "========================================="
echo "   Can't Stop - Dice Game Launcher"
echo "========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    echo "Please install Node.js 16 or higher"
    exit 1
fi

echo "Starting Backend Server..."
cd backend

# Install backend dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

# Start backend in background
python main.py &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID) on http://localhost:8000"

cd ..

echo ""
echo "Starting Frontend..."
cd frontend

# Install frontend dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start frontend
echo ""
echo "========================================="
echo "  Game is starting on http://localhost:3000"
echo "========================================="
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

npm run dev

# Cleanup: kill backend when frontend stops
kill $BACKEND_PID
