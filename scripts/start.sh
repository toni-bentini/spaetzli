#!/bin/bash
# Spaetzli Start Script
# Starts mock server, Rotki backend, and frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROTKI_DIR="$PROJECT_DIR/rotki"
FRONTEND_DIR="$ROTKI_DIR/frontend"

# Function to find a free port
find_free_port() {
    local start_port=$1
    local port=$start_port
    while lsof -i :$port >/dev/null 2>&1; do
        port=$((port + 1))
        if [ $port -gt $((start_port + 100)) ]; then
            echo "❌ Could not find free port" >&2
            exit 1
        fi
    done
    echo $port
}

echo "🐦 Starting Spaetzli"
echo "==================="
echo ""

# Check if setup was run
if [ ! -d "$ROTKI_DIR" ]; then
    echo "❌ Rotki not found. Please run setup first:"
    echo "   ./scripts/setup.sh"
    exit 1
fi

if [ ! -d "$ROTKI_DIR/.venv" ]; then
    echo "❌ Dependencies not installed. Please run setup first:"
    echo "   ./scripts/setup.sh"
    exit 1
fi

# Check for pnpm, install if missing
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm@latest-10 2>/dev/null || {
        echo "❌ Failed to install pnpm. Please install manually:"
        echo "   npm install -g pnpm"
        exit 1
    }
fi

# Find free ports
MOCK_PORT=$(find_free_port 8090)
ROTKI_PORT=$(find_free_port 4242)

echo "📍 Using ports: Mock=$MOCK_PORT, Rotki API=$ROTKI_PORT"
echo ""

# Kill any existing processes
pkill -f "spaetzli_mock_server" 2>/dev/null || true
pkill -f "rotkehlchen" 2>/dev/null || true
sleep 1

# Start mock server in background
echo "🚀 Starting mock premium server..."
cd "$ROTKI_DIR"
PYTHONPATH="$PROJECT_DIR" uv run python -m spaetzli_mock_server --port $MOCK_PORT > /tmp/spaetzli-mock.log 2>&1 &
MOCK_PID=$!

# Wait for mock server
echo "⏳ Waiting for mock server..."
for i in {1..15}; do
    if curl -s "http://localhost:$MOCK_PORT/health" > /dev/null 2>&1; then
        echo "✅ Mock server ready on port $MOCK_PORT"
        break
    fi
    sleep 1
done

# Start Rotki backend
echo "🚀 Starting Rotki backend..."
cd "$ROTKI_DIR"
SPAETZLI_MOCK_URL="http://localhost:$MOCK_PORT" uv run python -m rotkehlchen \
    --rest-api-port $ROTKI_PORT \
    --api-cors "http://localhost:*" > /tmp/spaetzli-rotki.log 2>&1 &
ROTKI_PID=$!

# Wait for Rotki
echo "⏳ Waiting for Rotki backend..."
for i in {1..30}; do
    if curl -s "http://localhost:$ROTKI_PORT/api/1/ping" > /dev/null 2>&1; then
        echo "✅ Rotki backend ready on port $ROTKI_PORT"
        break
    fi
    sleep 1
done

# Install frontend dependencies if needed
echo "🚀 Setting up frontend..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies (first time only)..."
    pnpm install 2>&1 | tail -5
fi

# Start frontend dev server
echo "🚀 Starting frontend..."
VITE_BACKEND_URL="http://localhost:$ROTKI_PORT" pnpm -w run dev > /tmp/spaetzli-frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontend to be ready
sleep 5

# Try to detect frontend port from log
FRONTEND_PORT=$(grep -oE "localhost:[0-9]+" /tmp/spaetzli-frontend.log 2>/dev/null | head -1 | cut -d: -f2 || echo "5173")

echo ""
echo "=============================================="
echo "✅ Spaetzli is running!"
echo ""
echo "🌐 Open in browser: http://localhost:$FRONTEND_PORT"
echo ""
echo "📍 Services:"
echo "   Frontend:    http://localhost:$FRONTEND_PORT"
echo "   Rotki API:   http://localhost:$ROTKI_PORT"
echo "   Mock Server: http://localhost:$MOCK_PORT"
echo ""
echo "💡 Go to Settings → Premium and enter any API key/secret"
echo ""
echo "📝 Logs: /tmp/spaetzli-*.log"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $MOCK_PID 2>/dev/null || true
    kill $ROTKI_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    pkill -f "spaetzli_mock_server" 2>/dev/null || true
    pkill -f "rotkehlchen" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait
wait
