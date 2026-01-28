#!/bin/bash
# Build Spaetzli as a standalone Electron app
# This creates a macOS .app with the patched Rotki + mock server embedded

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ROTKI_DIR="$PROJECT_DIR/rotki"

echo "🐦 Building Spaetzli App"
echo "========================"
echo ""

# Check prerequisites
if [ ! -d "$ROTKI_DIR" ]; then
    echo "❌ Run ./scripts/setup.sh first"
    exit 1
fi

command -v pnpm &> /dev/null || { echo "❌ pnpm required: npm i -g pnpm"; exit 1; }

cd "$ROTKI_DIR"

# Step 1: Build Python backend (rotki-core)
echo "📦 Building Python backend..."
uv run python package.py --build backend

# Step 2: Build frontend and package Electron app
echo "📦 Building frontend & Electron app..."
cd frontend
pnpm install
pnpm run electron:build

echo ""
echo "=============================================="
echo "✅ Build complete!"
echo ""
echo "📍 App location:"
ls -la "$ROTKI_DIR/frontend/app/dist/"*.dmg 2>/dev/null || \
ls -la "$ROTKI_DIR/frontend/app/dist/"*.app 2>/dev/null || \
echo "   $ROTKI_DIR/frontend/app/dist/"
echo "=============================================="
