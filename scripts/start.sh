#!/bin/bash
# Spaetzli Start Script
# Starts both the mock server and Rotki in one command

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROTKI_DIR="$PROJECT_DIR/rotki"
MOCK_PORT=8080

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

# Kill any existing processes on our ports
pkill -f "spaetzli_mock_server" 2>/dev/null || true
pkill -f "rotkehlchen" 2>/dev/null || true
sleep 1

# Start mock server in background (using rotki's venv which has our deps)
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
echo "🚀 Starting Rotki backend..."
cd "$ROTKI_DIR"
SPAETZLI_MOCK_URL="http://localhost:$MOCK_PORT" uv run python -m rotkehlchen --api-port 4242 --api-cors http://localhost:* &
ROTKI_PID=$!

# Give Rotki a moment to start
sleep 5

echo ""
echo "✅ Both services started!"
echo ""
echo "📍 Rotki API:     http://localhost:4242"
echo "📍 Mock Server:   http://localhost:$MOCK_PORT"
echo ""
echo "💡 To use the web UI, you have two options:"
echo ""
echo "   Option A: Use the Rotki frontend (recommended)"
echo "   1. Open a new terminal"
echo "   2. cd $ROTKI_DIR/frontend/app"
echo "   3. npm install && npm run dev"
echo "   4. Open http://localhost:8080"
echo ""
echo "   Option B: Use the installed Rotki app"
echo "   The app will connect to localhost:4242 automatically"
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
