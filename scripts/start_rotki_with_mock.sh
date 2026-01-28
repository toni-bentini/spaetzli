#!/bin/bash
# Start Rotki configured to use the mock premium server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if mock server is running
if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "⚠️  Mock server not running. Start it first with:"
    echo "   ./scripts/start_mock_server.sh"
    exit 1
fi

echo "🚀 Starting Rotki with mock premium server..."

# Set environment to use local mock (requires patching Rotki)
export ROTKI_PREMIUM_MOCK_ENABLED=1

cd "$PROJECT_DIR"
python -m rotkehlchen --api-cors "http://localhost:*" "$@"
