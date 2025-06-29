#!/usr/bin/env python3
"""
Launch Streamlit Dashboard for WhatsApp AI Assistant
"""

import subprocess
import sys
import os
from config.settings import settings

def main():
    """Launch the Streamlit dashboard"""
    print("🚀 Starting WhatsApp AI Assistant Dashboard...")
    
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        print("❌ Streamlit not found. Please install requirements:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # Launch streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "dashboard/streamlit_app.py",
        "--server.port", str(settings.dashboard_port),
        "--server.address", settings.dashboard_host,
        "--server.headless", "true"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")

if __name__ == "__main__":
    main() 