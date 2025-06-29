#!/bin/bash

# WhatsApp AI Assistant - Quick Start Script

echo "🤖 WhatsApp AI Assistant - Quick Start"
echo "========================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    echo "   cp .env.example .env"
    echo "   Then edit .env with your Gemini API key"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔄 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "🔄 Installing dependencies..."
pip install -r requirements.txt

# Check if whatsapp-mcp is running
echo "🔄 Checking WhatsApp MCP server..."
if ! curl -s http://localhost:3333/health > /dev/null 2>&1; then
    echo "⚠️  WhatsApp MCP server not detected on port 3333"
    echo "   Please start it first:"
    echo "   cd whatsapp-mcp && go run ."
    echo ""
    read -p "Press Enter when MCP server is running, or Ctrl+C to exit..."
fi

# Start the assistant
echo "🚀 Starting WhatsApp AI Assistant..."
echo "💡 Dashboard will be available at: http://localhost:8501"
echo "💡 To start dashboard: python run_dashboard.py (in another terminal)"
echo "========================================"

python main.py 