#!/bin/bash

echo "🚀 Starting WhatsApp Bridge for AI Assistant..."
echo "=============================================="

# Check if Go is installed
if ! command -v go &> /dev/null; then
    echo "❌ Go is not installed. Please install Go first."
    echo "💡 Download from: https://golang.org/dl/"
    exit 1
fi

echo "✅ Go found: $(go version)"

# Navigate to whatsapp-bridge directory
BRIDGE_DIR="whatsapp-mcp/whatsapp-bridge"

if [ ! -d "$BRIDGE_DIR" ]; then
    echo "❌ WhatsApp bridge directory not found: $BRIDGE_DIR"
    echo "💡 Make sure you're running this from the project root"
    exit 1
fi

cd "$BRIDGE_DIR" || exit 1

echo "🔄 Setting up environment for Windows..."

# Set CGO environment variables for Windows
export CGO_ENABLED=1
export CC=gcc
export CXX=g++

# Try to detect if we're on Windows and set appropriate flags
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    echo "🖥️  Windows environment detected"
    echo "⚠️  If you get CGO compilation errors, try these solutions:"
    echo "   1. Install w64devkit: https://github.com/skeeto/w64devkit/releases"
    echo "   2. Use Windows Command Prompt instead of Git Bash"
    echo "   3. Use WSL2 with Ubuntu"
    echo ""
fi

echo "🔄 Starting WhatsApp bridge..."
echo "📱 On first run, scan the QR code with your WhatsApp app"
echo "🌐 Bridge will run on http://localhost:3334"
echo "=============================================="

# Try to run with error handling
if ! go run main.go; then
    echo ""
    echo "❌ Failed to start WhatsApp bridge"
    echo ""
    echo "💡 Common fixes for Windows CGO errors:"
    echo "   1. Install TDM-GCC: https://jmeubank.github.io/tdm-gcc/"
    echo "   2. Install w64devkit: https://github.com/skeeto/w64devkit/releases"
    echo "   3. Use Windows Command Prompt:"
    echo "      cd \"whatsapp-mcp\\whatsapp-bridge\""
    echo "      go run main.go"
    echo "   4. Use WSL2:"
    echo "      wsl"
    echo "      sudo apt install golang-go"
    echo "      cd /mnt/c/Users/Kethan/Documents/projects/Learning/whatsapp\\ agent/"
    echo "      cd whatsapp-mcp/whatsapp-bridge"
    echo "      go run main.go"
    echo ""
    exit 1
fi 