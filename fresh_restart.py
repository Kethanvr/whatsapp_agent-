#!/usr/bin/env python3
"""
Fresh Restart - Reset bot memory and start fresh
"""

import sys
import os
import time
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.whatsapp_client import whatsapp_client
from core.message_processor import message_processor

def fresh_restart():
    """Reset everything and start fresh"""
    logger.info("🔄 FRESH RESTART - Resetting all bot memory")
    logger.info("=" * 60)
    
    # Reset message tracking completely
    whatsapp_client._last_message_ids.clear()
    whatsapp_client._startup_time = time.time()
    
    # Reset message processor 
    message_processor.processed_message_ids.clear()
    message_processor.message_history.clear()
    
    logger.info("✅ All message tracking RESET")
    logger.info(f"✅ New startup time: {whatsapp_client._startup_time}")
    logger.info("✅ Ready to process ONLY brand new messages")
    
    # Wait a moment for system to stabilize
    logger.info("⏳ Waiting 3 seconds for system to stabilize...")
    time.sleep(3)
    
    # Test connectivity
    if whatsapp_client.health_check():
        logger.info("✅ WhatsApp bridge connected")
    else:
        logger.error("❌ Bridge connection failed!")
        return False
    
    logger.info("🚀 Starting FRESH message processor...")
    logger.info("📱 Send a NEW message now with: !ask, @ai, @bot, or >")
    
    # Start fresh polling
    message_processor.start_polling()
    
    return True

if __name__ == "__main__":
    fresh_restart() 