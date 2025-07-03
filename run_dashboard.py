#!/usr/bin/env python3
"""
Launch Streamlit Dashboard for WhatsApp AI Assistant
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

# Force reload environment variables
load_dotenv(override=True)

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
    
    # Import settings after environment is loaded
    from config.settings import settings
    dashboard_port = int(os.environ.get("PORT", settings.dashboard_port))
    
    # Launch streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "dashboard/streamlit_app.py",
        "--server.port", str(dashboard_port),
        "--server.address", settings.dashboard_host,
        "--server.headless", "true"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped")

if __name__ == "__main__":
    main() 