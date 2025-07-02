#!/usr/bin/env python3
"""
Force Test - Bypass FromMe check and force process a message
"""

import sys
import os
import time
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.whatsapp_client import whatsapp_client
from core.message_processor import message_processor

def force_test_message():
    """Force test message processing"""
    logger.info("🔧 FORCE TEST - Bypassing FromMe check")
    
    # Reset grace period
    whatsapp_client._startup_time = time.time() - 10  # 10 seconds ago
    
    # Get authorized chat
    chats = whatsapp_client.get_chats()
    auth_chat = None
    for chat in chats[:5]:
        if "917483531255" in chat.id or "916360751048" in chat.id:
            auth_chat = chat
            break
    
    if not auth_chat:
        logger.error("❌ No authorized chat found")
        return
    
    logger.info(f"🎯 Testing with chat: {auth_chat.id}")
    
    # Get recent messages
    messages = whatsapp_client.get_messages(auth_chat.id, limit=3)
    
    for msg in messages:
        logger.info(f"📨 Message: '{msg.text}' | FromMe: {msg.is_from_me}")
        
        # Force check trigger (ignore FromMe)
        if any(trigger.lower() in msg.text.lower() for trigger in ['!ask', '@ai', '@bot', '>']):
            logger.info(f"🎯 FORCING processing of: '{msg.text}'")
            
            # Manually trigger processing
            try:
                # Override FromMe temporarily
                original_from_me = msg.is_from_me
                msg.is_from_me = False
                
                message_processor._process_single_message(msg)
                
                # Restore original
                msg.is_from_me = original_from_me
                
                logger.info(f"✅ Force processing completed!")
                return
                
            except Exception as e:
                logger.error(f"❌ Force processing failed: {e}")
    
    logger.warning("⚠️ No triggered messages found to force process")

if __name__ == "__main__":
    force_test_message() 