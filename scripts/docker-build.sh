#!/bin/bash
# Build Spaetzli Docker image
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🐦 Building Spaetzli Docker Image"
echo "================================="
echo ""

# Check if rotki is cloned
if [ ! -d "$PROJECT_DIR/rotki" ]; then
    echo "📥 Cloning Rotki..."
    git clone --depth 1 https://github.com/rotki/rotki.git "$PROJECT_DIR/rotki"
fi

# Build the image
cd "$PROJECT_DIR"
docker build -t spaetzli:latest -f docker/Dockerfile .

echo ""
echo "✅ Build complete!"
echo ""
echo "To run:"
echo "  docker run -p 8080:80 -v spaetzli-data:/data spaetzli:latest"
echo ""
echo "Or with docker-compose:"
echo "  cd docker && docker-compose up"
echo ""
echo "Then open http://localhost:8080"
