#!/bin/bash
set -e

# Use PORT from environment or default to 10000
export PORT=${PORT:-10000}

echo "🚀 Starting WhatsApp AI Agent Production Environment"

# Start WhatsApp Bridge in background
echo "📱 Starting WhatsApp Bridge..."
/usr/local/bin/whatsapp-bridge &
BRIDGE_PID=$!

# Wait for bridge to be ready
echo "⏳ Waiting for WhatsApp Bridge to initialize..."
for i in {1..30}; do
    if curl -f http://localhost:${PORT}/health 2>/dev/null; then
        echo "✅ WhatsApp Bridge is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ WhatsApp Bridge failed to start"
        exit 1
    fi
    sleep 2
done

# Start MCP Server in background
echo "🔧 Starting MCP Server..."
cd /app/mcp-server && PORT=3334 python main.py &
MCP_PID=$!

# Wait for MCP server to be ready
echo "⏳ Waiting for MCP Server to initialize..."
for i in {1..15}; do
    if curl -f http://localhost:3334/health 2>/dev/null; then
        echo "✅ MCP Server is ready"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ MCP Server failed to start"
        kill $BRIDGE_PID 2>/dev/null || true
        exit 1
    fi
    sleep 2
done

# Start main application
echo "🤖 Starting Main AI Agent..."
cd /app
exec python main.py --host 0.0.0.0 --port $PORT

# Cleanup function
cleanup() {
    echo "🛑 Shutting down services..."
    kill $MCP_PID 2>/dev/null || true
    kill $BRIDGE_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT 