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

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv. Please install manually:"
        echo "   brew install uv"
        exit 1
    fi
fi
echo "✅ Found uv"

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

# Use uv to run Python (it will fetch Python 3.11 if needed)
uv run --python 3.11 python "$SCRIPT_DIR/apply_patch.py" "$ROTKI_DIR/rotkehlchen/premium/premium.py"

# Create venv with Python 3.11 and install dependencies
echo "📦 Creating Python 3.11 environment and installing dependencies..."
echo "   (This may take several minutes on first run)"
cd "$ROTKI_DIR"

# Force uv to use Python 3.11
uv venv --python 3.11 .venv 2>/dev/null || uv venv .venv

# Sync dependencies
echo "   Syncing Rotki dependencies..."
uv sync 2>&1 | tail -15

# Install mock server dependencies
echo "📦 Installing mock server dependencies..."
uv pip install fastapi uvicorn python-multipart 2>&1 | tail -5

cd "$PROJECT_DIR"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start Rotki with premium features:"
echo "  ./scripts/start.sh"
echo ""
