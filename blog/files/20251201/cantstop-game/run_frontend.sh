#!/bin/bash
cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo ""
echo "Starting frontend on http://localhost:3000"
echo "Press Ctrl+C to stop"
echo ""

npm run dev
