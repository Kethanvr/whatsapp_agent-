#!/usr/bin/env python3
"""
Instant Bot - No grace period, processes all authorized messages immediately
"""

import sys
import os
import time
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.message_processor import message_processor
from core.whatsapp_client import whatsapp_client

def start_instant_bot():
    """Start bot with immediate processing"""
    logger.info("⚡ INSTANT BOT - Starting with immediate message processing")
    
    # Reset everything
    whatsapp_client._last_message_ids.clear()
    whatsapp_client._startup_time = time.time() - 3600  # 1 hour ago to catch all recent messages
    message_processor.processed_message_ids.clear()
    
    logger.info("🔧 All tracking reset, startup time set to 1 hour ago")
    logger.info("⚡ Processing ALL recent messages immediately...")
    
    # Start with no grace period
    message_processor.start_polling()

if __name__ == "__main__":
    start_instant_bot() 