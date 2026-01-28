#!/bin/bash
# Spaetzli Start Script
# Starts mock server, Rotki backend, and frontend

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROTKI_DIR="$PROJECT_DIR/rotki"
FRONTEND_DIR="$ROTKI_DIR/frontend/app"

# Fixed ports for reliability
MOCK_PORT=18090
ROTKI_PORT=14242
FRONTEND_PORT=15173

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

# Check for pnpm
if ! command -v pnpm &> /dev/null; then
    echo "📦 Installing pnpm..."
    npm install -g pnpm@latest-10
fi

# Kill any existing processes on our ports
echo "🧹 Cleaning up old processes..."
pkill -f "spaetzli_mock_server" 2>/dev/null || true
pkill -f "rotkehlchen" 2>/dev/null || true
lsof -ti :$MOCK_PORT | xargs kill -9 2>/dev/null || true
lsof -ti :$ROTKI_PORT | xargs kill -9 2>/dev/null || true
lsof -ti :$FRONTEND_PORT | xargs kill -9 2>/dev/null || true
sleep 2

echo "📍 Using ports: Mock=$MOCK_PORT, Rotki=$ROTKI_PORT, Frontend=$FRONTEND_PORT"
echo ""

# Start mock server
echo "🚀 Starting mock premium server..."
cd "$ROTKI_DIR"
PYTHONPATH="$PROJECT_DIR" uv run python -m spaetzli_mock_server --port $MOCK_PORT > /tmp/spaetzli-mock.log 2>&1 &
MOCK_PID=$!

# Wait for mock server
echo "⏳ Waiting for mock server..."
for i in {1..15}; do
    if curl -s "http://localhost:$MOCK_PORT/health" > /dev/null 2>&1; then
        echo "✅ Mock server ready"
        break
    fi
    sleep 1
done

# Start Rotki backend
echo "🚀 Starting Rotki backend..."
cd "$ROTKI_DIR"
SPAETZLI_MOCK_URL="http://localhost:$MOCK_PORT" uv run python -m rotkehlchen \
    --rest-api-port $ROTKI_PORT \
    --api-cors "http://localhost:*,http://127.0.0.1:*" > /tmp/spaetzli-rotki.log 2>&1 &
ROTKI_PID=$!

# Wait for Rotki
echo "⏳ Waiting for Rotki backend..."
for i in {1..30}; do
    if curl -s "http://localhost:$ROTKI_PORT/api/1/ping" > /dev/null 2>&1; then
        echo "✅ Rotki backend ready"
        break
    fi
    sleep 1
done

# Install frontend dependencies if needed
cd "$ROTKI_DIR/frontend"
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies (first time, please wait)..."
    pnpm install 2>&1 | tail -10
fi

# Create .env.local with correct URLs
echo "🔧 Configuring frontend..."
cat > "$FRONTEND_DIR/.env.local" << EOF
VITE_BACKEND_URL=http://127.0.0.1:$ROTKI_PORT
VITE_COLIBRI_URL=http://127.0.0.1:$ROTKI_PORT
EOF

# Start frontend
echo "🚀 Starting frontend..."
cd "$FRONTEND_DIR"
npx vite --port $FRONTEND_PORT --host > /tmp/spaetzli-frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 3

echo ""
echo "=============================================="
echo "✅ Spaetzli is running!"
echo ""
echo "🌐 Open: http://localhost:$FRONTEND_PORT"
echo ""
echo "📍 Services:"
echo "   Frontend:    http://localhost:$FRONTEND_PORT"
echo "   Rotki API:   http://localhost:$ROTKI_PORT"
echo "   Mock Server: http://localhost:$MOCK_PORT"
echo ""
echo "💡 Enter any API key/secret for premium"
echo "   Example: key='test' secret='dGVzdA=='"
echo ""
echo "📝 Logs: /tmp/spaetzli-*.log"
echo "=============================================="
echo ""
echo "Press Ctrl+C to stop"

# Cleanup handler
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $MOCK_PID $ROTKI_PID $FRONTEND_PID 2>/dev/null || true
    pkill -f "spaetzli_mock_server" 2>/dev/null || true
    pkill -f "rotkehlchen" 2>/dev/null || true
    rm -f "$FRONTEND_DIR/.env.local"
    exit 0
}
trap cleanup SIGINT SIGTERM

wait
