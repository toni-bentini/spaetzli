#!/bin/bash
# Spaetzli Start Script
# Starts both the mock server and Rotki in one command

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROTKI_DIR="$PROJECT_DIR/rotki"

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

# Check if uv venv exists
if [ ! -d "$ROTKI_DIR/.venv" ]; then
    echo "❌ Dependencies not installed. Please run setup first:"
    echo "   ./scripts/setup.sh"
    exit 1
fi

# Find free ports
MOCK_PORT=$(find_free_port 8090)
ROTKI_PORT=$(find_free_port 4242)

echo "📍 Using ports: Mock=$MOCK_PORT, Rotki=$ROTKI_PORT"
echo ""

# Kill any existing spaetzli processes
pkill -f "spaetzli_mock_server" 2>/dev/null || true
pkill -f "rotkehlchen" 2>/dev/null || true
sleep 1

# Start mock server in background
echo "🚀 Starting mock premium server on port $MOCK_PORT..."
cd "$ROTKI_DIR"
PYTHONPATH="$PROJECT_DIR" uv run python -m spaetzli_mock_server --port $MOCK_PORT &
MOCK_PID=$!

# Wait for mock server to be ready
echo "⏳ Waiting for mock server..."
for i in {1..15}; do
    if curl -s "http://localhost:$MOCK_PORT/health" > /dev/null 2>&1; then
        echo "✅ Mock server ready"
        break
    fi
    sleep 1
done

# Start Rotki
echo "🚀 Starting Rotki backend on port $ROTKI_PORT..."
cd "$ROTKI_DIR"
SPAETZLI_MOCK_URL="http://localhost:$MOCK_PORT" uv run python -m rotkehlchen \
    --rest-api-port $ROTKI_PORT \
    --api-cors "http://localhost:*" &
ROTKI_PID=$!

# Give Rotki a moment to start
sleep 5

echo ""
echo "✅ Both services started!"
echo ""
echo "📍 Rotki API:     http://localhost:$ROTKI_PORT"
echo "📍 Mock Server:   http://localhost:$MOCK_PORT"
echo ""
echo "💡 To use the web UI:"
echo "   1. cd $ROTKI_DIR/frontend/app"
echo "   2. pnpm install && pnpm run dev"
echo "   3. Open the URL shown (usually http://localhost:5173)"
echo "   4. The frontend will connect to Rotki on port $ROTKI_PORT"
echo ""
echo "Press Ctrl+C to stop services"
echo ""

# Handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $MOCK_PID 2>/dev/null || true
    kill $ROTKI_PID 2>/dev/null || true
    pkill -f "spaetzli_mock_server" 2>/dev/null || true
    pkill -f "rotkehlchen" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait
