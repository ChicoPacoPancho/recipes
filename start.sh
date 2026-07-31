#!/bin/bash
# Development startup script
# Starts both the backend and frontend dev servers

set -e

echo "🍳 Starting Family Cookbook..."

# Check Python dependencies
if ! pip show flask > /dev/null 2>&1; then
    echo "📦 Installing Python dependencies..."
    pip install -r backend/requirements.txt
fi

# Check Node dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start backend
echo "🔧 Starting backend on http://localhost:5000..."
python -m backend.app &
BACKEND_PID=$!

# Start frontend dev server
echo "🎨 Starting frontend on http://localhost:5173..."
cd frontend && npm run dev &
FRONTEND_PID=$!

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

echo ""
echo "✅ Family Cookbook is running!"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop."

wait
