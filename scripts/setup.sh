#!/bin/bash
# Spaetzli Setup Script
# Sets up everything needed to run Rotki with the mock premium server

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROTKI_DIR="$PROJECT_DIR/rotki"

echo "🐦 Spaetzli Setup"
echo "================="
echo ""

# Check for uv (recommended) or Python 3.11+
if command -v uv &> /dev/null; then
    echo "✅ Found uv package manager"
    USE_UV=1
elif python3 --version 2>&1 | grep -q "3.11\|3.12"; then
    echo "✅ Found compatible Python"
    USE_UV=0
else
    echo "❌ This script requires either:"
    echo "   - uv (recommended): brew install uv"
    echo "   - Python 3.11+: brew install python@3.11"
    exit 1
fi

# Clone Rotki if not present
if [ ! -d "$ROTKI_DIR" ]; then
    echo "📥 Cloning Rotki from source..."
    git clone --depth 1 https://github.com/rotki/rotki.git "$ROTKI_DIR"
else
    echo "✅ Rotki source already present"
fi

# Apply the Spaetzli patch to Rotki
echo "🔧 Applying Spaetzli patch to Rotki..."
cd "$ROTKI_DIR"
if [ "$USE_UV" = "1" ]; then
    uv run --no-project python "$SCRIPT_DIR/apply_patch.py" "$ROTKI_DIR/rotkehlchen/premium/premium.py"
else
    python3 "$SCRIPT_DIR/apply_patch.py" "$ROTKI_DIR/rotkehlchen/premium/premium.py"
fi

# Install Rotki dependencies (this also creates the venv)
echo "📦 Installing Rotki dependencies (this may take several minutes)..."
cd "$ROTKI_DIR"

if [ "$USE_UV" = "1" ]; then
    echo "   Syncing with uv..."
    uv sync 2>&1 | tail -10
else
    python3 -m pip install -e .
fi

# Install mock server dependencies into Rotki's venv
echo "📦 Installing mock server dependencies..."
cd "$PROJECT_DIR"
if [ "$USE_UV" = "1" ]; then
    cd "$ROTKI_DIR"
    uv pip install fastapi uvicorn python-multipart 2>&1 | tail -5
else
    python3 -m pip install --quiet fastapi uvicorn python-multipart
fi

cd "$PROJECT_DIR"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start Rotki with premium features:"
echo "  ./scripts/start.sh"
echo ""
