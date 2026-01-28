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

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check for pip
if ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip is required but not installed."
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
PREMIUM_PY="$ROTKI_DIR/rotkehlchen/premium/premium.py"

if grep -q "SPAETZLI_MOCK_URL" "$PREMIUM_PY" 2>/dev/null; then
    echo "✅ Patch already applied"
else
    # Backup original
    cp "$PREMIUM_PY" "$PREMIUM_PY.backup"
    
    # Apply patch - add mock URL support after the staging check
    sed -i.tmp '
/rotki_base_url = .staging.rotki.com./a\
\
        # Support custom mock server via environment variables (Spaetzli)\
        if mock_url := os.environ.get('"'"'SPAETZLI_MOCK_URL'"'"'):\
            log.info(f'"'"'Using Spaetzli mock server at {mock_url}'"'"')\
            self.rotki_api = f'"'"'{mock_url}/api/{self.apiversion}/'"'"'\
            self.rotki_web = f'"'"'{mock_url}/webapi/{self.apiversion}/'"'"'\
            self.rotki_nest = f'"'"'{mock_url}/nest/{self.apiversion}/'"'"'\
        else:
' "$PREMIUM_PY"
    
    # Also need to wrap the original URLs in else block - simpler approach: use our patched file
    cp "$PROJECT_DIR/rotkehlchen/premium/premium.py" "$PREMIUM_PY"
    rm -f "$PREMIUM_PY.tmp"
    
    echo "✅ Patch applied"
fi

# Install mock server dependencies
echo "📦 Installing mock server dependencies..."
python3 -m pip install -q fastapi uvicorn python-multipart

# Install Rotki dependencies (this can take a while)
echo "📦 Installing Rotki dependencies (this may take a few minutes)..."
cd "$ROTKI_DIR"
python3 -m pip install -q -e . 2>/dev/null || {
    echo "⚠️  Some dependencies may need manual installation."
    echo "   Try: cd $ROTKI_DIR && pip install -e ."
}

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start Rotki with premium features:"
echo "  1. Run: $SCRIPT_DIR/start.sh"
echo ""
echo "Or manually:"
echo "  Terminal 1: python3 -m spaetzli_mock_server --port 8080"
echo "  Terminal 2: cd $ROTKI_DIR && SPAETZLI_MOCK_URL=http://localhost:8080 python3 -m rotkehlchen"
echo "  Then open: http://localhost:4242"
