#!/bin/bash
# Spaetzli One-Line Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/toni-bentini/spaetzli/main/install.sh | bash

set -e

REPO="https://github.com/toni-bentini/spaetzli.git"
INSTALL_DIR="$HOME/spaetzli"

echo ""
echo "🐦 Spaetzli Installer"
echo "====================="
echo ""

# Check for required tools
check_dependency() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 is required but not installed."
        echo "   Install with: $2"
        exit 1
    fi
}

check_dependency "git" "brew install git"
check_dependency "curl" "brew install curl"

# Check for uv or offer to install
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv (Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo "📂 Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --ff-only 2>/dev/null || {
        echo "⚠️  Could not update, using existing version"
    }
else
    echo "📥 Cloning Spaetzli..."
    git clone --depth 1 "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Run setup
echo ""
./scripts/setup.sh

echo ""
echo "=============================================="
echo "✅ Spaetzli installed to: $INSTALL_DIR"
echo ""
echo "To start Spaetzli:"
echo "  cd $INSTALL_DIR && ./scripts/start.sh"
echo ""
echo "Or run this one-liner anytime:"
echo "  cd ~/spaetzli && ./scripts/start.sh"
echo "=============================================="
echo ""

# Ask if user wants to start now
read -p "Start Spaetzli now? [Y/n] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    ./scripts/start.sh
fi
