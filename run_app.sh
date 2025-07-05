#!/bin/bash

# =============================================
#         WhatsApp AI Assistant Starter
# =============================================
# This script starts the Go bridge in the
# background and then the Python bot in the
# foreground.
# =============================================

# Function to clean up background processes on exit
cleanup() {
    echo "Shutting down background processes..."
    kill $bridge_pid
    exit
}

# Trap Ctrl+C (SIGINT) and call the cleanup function
trap cleanup SIGINT

# --- Start the Go WhatsApp Bridge in the background ---
echo "🚀 Starting Go WhatsApp Bridge in the background..."
./start_whatsapp_bridge.sh &
bridge_pid=$!

# Give the bridge a moment to initialize
echo "⏳ Waiting for the bridge to start..."
sleep 10

# --- Start the Python AI Bot in the foreground ---
echo "🤖 Starting Python AI Bot..."
python enhanced_instant_bot.py

# Call cleanup when the script finishes
cleanup