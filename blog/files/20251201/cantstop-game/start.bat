@echo off
REM Can't Stop Game - Windows Startup Script

echo =========================================
echo    Can't Stop - Dice Game Launcher
echo =========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if Node is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed
    echo Please install Node.js 16 or higher
    pause
    exit /b 1
)

echo Starting Backend Server...
cd backend

REM Install backend dependencies if needed
if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

call venv\Scripts\activate
pip install -q -r requirements.txt

REM Start backend in background
start "Can't Stop Backend" cmd /c python main.py
echo Backend started on http://localhost:8000

cd ..
echo.

echo Starting Frontend...
cd frontend

REM Install frontend dependencies if needed
if not exist node_modules (
    echo Installing npm dependencies...
    call npm install
)

echo.
echo =========================================
echo   Game is starting on http://localhost:3000
echo =========================================
echo.
echo Press Ctrl+C in this window to stop servers
echo.

call npm run dev
