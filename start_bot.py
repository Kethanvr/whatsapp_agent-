#!/usr/bin/env python3
"""
Simple Bot Startup Script - Start WhatsApp AI Bot with clear status
"""

import subprocess
import sys
import time
from loguru import logger

def main():
    """Start the WhatsApp AI Bot"""
    logger.remove()  # Remove default logger
    logger.add(sys.stdout, format="{time:HH:mm:ss} | {level} | {message}", colorize=True)
    
    logger.info("🚀 Starting WhatsApp AI Bot...")
    logger.info("🔧 Fixed: Bot now only processes NEW messages (not historical)")
    logger.info("📱 Ready for messages with: @ai, !ask, @bot, >")
    logger.info("🔒 Authorized numbers: +917483531255, +916360751048")
    logger.info("=" * 60)
    
    try:
        # Start the main bot
        subprocess.run([sys.executable, "main.py"], check=True)
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot failed: {e}")

if __name__ == "__main__":
    main() 