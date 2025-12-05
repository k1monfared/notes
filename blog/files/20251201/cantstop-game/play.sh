#!/bin/bash

# Can't Stop Game - One-Command Launcher
# Just run: ./play.sh

echo "🎲 Starting Can't Stop Game..."
echo ""

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Install backend dependencies silently
echo "⚙️  Setting up backend..."
cd "$DIR/backend"
python3 -m pip install --user -q fastapi uvicorn pydantic 2>/dev/null

# Start backend in background
python3 main.py > /tmp/cantstop-backend.log 2>&1 &
BACKEND_PID=$!
echo "✓ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
sleep 2

# Install frontend dependencies if needed
cd "$DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "⚙️  Setting up frontend (first time only)..."
    npm install --silent > /dev/null 2>&1
fi

echo "✓ Frontend starting..."
echo ""
echo "========================================="
echo "  🎮 Game opening in browser..."
echo "  📍 URL: http://localhost:3000"
echo "========================================="
echo ""
echo "Press Ctrl+C to stop the game"
echo ""

# Start frontend (this will block)
npm run dev &
FRONTEND_PID=$!

# Wait a moment for frontend to start, then open browser
sleep 3
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000 2>/dev/null &
elif command -v open > /dev/null; then
    open http://localhost:3000 2>/dev/null &
elif command -v wslview > /dev/null; then
    wslview http://localhost:3000 2>/dev/null &
fi

# Wait for frontend to finish
wait $FRONTEND_PID

# Cleanup
echo ""
echo "🛑 Stopping game..."
kill $BACKEND_PID 2>/dev/null
echo "✓ Stopped"
