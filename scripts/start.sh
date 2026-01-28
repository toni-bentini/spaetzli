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
    echo "   $SCRIPT_DIR/setup.sh"
    exit 1
fi

# Kill any existing processes on our ports
pkill -f "spaetzli_mock_server" 2>/dev/null || true
pkill -f "rotkehlchen" 2>/dev/null || true
sleep 1

# Start mock server in background
echo "🚀 Starting mock premium server on port $MOCK_PORT..."
cd "$PROJECT_DIR"
python3 -m spaetzli_mock_server --port $MOCK_PORT &
MOCK_PID=$!

# Wait for mock server to be ready
echo "⏳ Waiting for mock server..."
for i in {1..10}; do
    if curl -s "http://localhost:$MOCK_PORT/health" > /dev/null 2>&1; then
        echo "✅ Mock server ready"
        break
    fi
    sleep 1
done

# Start Rotki
echo "🚀 Starting Rotki..."
cd "$ROTKI_DIR"
SPAETZLI_MOCK_URL="http://localhost:$MOCK_PORT" python3 -m rotkehlchen &
ROTKI_PID=$!

echo ""
echo "✅ Both services started!"
echo ""
echo "📍 Rotki UI:      http://localhost:4242"
echo "📍 Mock Server:   http://localhost:$MOCK_PORT"
echo ""
echo "💡 Enter any API key/secret in Rotki's premium settings"
echo "   (Settings → Premium → any values work)"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Handle shutdown
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $MOCK_PID 2>/dev/null || true
    kill $ROTKI_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

# Wait for either process to exit
wait
