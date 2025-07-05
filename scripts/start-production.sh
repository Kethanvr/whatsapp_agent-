#!/bin/bash
set -e

# Render provides the PORT env var, which the Go bridge will use.
# The python servers have hardcoded ports.
export PORT=${PORT:-10000}

# --- Cleanup function called on exit ---
# Ensures all background processes are terminated when the script exits.
cleanup() {
    echo "🛑 Shutting down services..."
    # Kill processes individually.
    if [ -n "$AGENT_PID" ]; then kill "$AGENT_PID"; fi
    if [ -n "$MCP_PID" ]; then kill "$MCP_PID"; fi
    if [ -n "$BRIDGE_PID" ]; then kill "$BRIDGE_PID"; fi
    exit 0
}
trap cleanup SIGTERM SIGINT

echo "🚀 Starting WhatsApp AI Agent Production Environment"

# --- 1. Start WhatsApp Bridge (Go) ---
echo "📱 Starting WhatsApp Bridge..."
# The Go app is built to listen on the PORT env var.
/usr/local/bin/whatsapp-bridge &
BRIDGE_PID=$!

# Wait for bridge to be ready.
echo "⏳ Waiting for WhatsApp Bridge to initialize..."
export BRIDGE_SERVER_URL="http://localhost:${PORT}"
for i in {1..30}; do
    if curl -s -f "${BRIDGE_SERVER_URL}/health" > /dev/null; then
        echo "✅ WhatsApp Bridge is ready on port ${PORT}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ WhatsApp Bridge failed to start"
        exit 1
    fi
    sleep 2
done

# --- 2. Start MCP Server (Python/FastAPI) ---
MCP_PORT=3334
echo "🔧 Starting MCP Server..."
# This server acts as a proxy between the main agent and the Go bridge.
cd /app/whatsapp-mcp/whatsapp-mcp-server && python main.py &
MCP_PID=$!

# Wait for MCP server to be ready.
echo "⏳ Waiting for MCP Server to initialize..."
for i in {1..15}; do
    if curl -s -f "http://localhost:${MCP_PORT}/health" > /dev/null; then
        echo "✅ MCP Server is ready on port ${MCP_PORT}"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ MCP Server failed to start"
        exit 1 # trap will handle cleanup
    fi
    sleep 2
done

# --- 3. Start Main AI Agent (Python/FastAPI) ---
AGENT_PORT=8503
echo "🤖 Starting Main AI Agent..."
# This is the core application with the message processing loop.
cd /app
python main.py --host 0.0.0.0 --port ${AGENT_PORT} &
AGENT_PID=$!

# Wait for main agent to be ready.
echo "⏳ Waiting for Main AI Agent to initialize..."
for i in {1..15}; do
    if curl -s -f "http://localhost:${AGENT_PORT}/health" > /dev/null; then
        echo "✅ Main AI Agent is ready on port ${AGENT_PORT}"
        break
    fi
    if [ $i -eq 15 ]; then
        echo "❌ Main AI Agent failed to start"
        exit 1 # trap will handle cleanup
    fi
    sleep 2
done

echo "🎉 All services are running. Waiting for signals to shutdown."

# --- Wait for any background job to exit ---
# The script will pause here. If any of the services crash, `wait -n` will return.
# The script will then exit, and the `cleanup` trap will be triggered.
wait -n

exit $? 