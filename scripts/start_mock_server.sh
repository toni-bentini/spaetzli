#!/bin/bash
# Start the Spaetzli mock premium server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR/spaetzli_mock_server"

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🍝 Starting Spaetzli Mock Premium Server..."
python -m spaetzli_mock_server "$@"
