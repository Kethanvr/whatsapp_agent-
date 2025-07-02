#!/usr/bin/env python3
"""
Live Debug - See exactly what's happening with message polling
"""

import sys
import os
import time
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.whatsapp_client import whatsapp_client
from config.settings import settings

def live_debug():
    """Live debugging of message polling"""
    logger.info("🔍 LIVE DEBUG - Real-time message analysis")
    logger.info("=" * 60)
    
    # Test connectivity
    if not whatsapp_client.health_check():
        logger.error("❌ Bridge not connected!")
        return
    
    logger.info("✅ Bridge connected - starting live analysis...")
    logger.info(f"🔒 Authorized numbers: {settings.authorized_number_list}")
    logger.info(f"🎯 Triggers: {settings.trigger_list}")
    logger.info(f"⏰ Current time: {time.time()}")
    logger.info(f"⏰ Bot startup: {whatsapp_client._startup_time}")
    logger.info(f"⏰ Time since startup: {time.time() - whatsapp_client._startup_time:.1f}s")
    
    # Get chats and find authorized ones
    logger.info("\n1️⃣ Checking chat discovery...")
    chats = whatsapp_client.get_chats()
    authorized_chats = []
    
    for chat in chats[:10]:  # Check first 10
        is_auth = any(auth.replace('+', '').strip() in chat.id for auth in settings.authorized_number_list)
        if is_auth:
            authorized_chats.append(chat)
            logger.info(f"🔒 AUTHORIZED CHAT: {chat.id} - {chat.name}")
    
    if not authorized_chats:
        logger.error("❌ NO AUTHORIZED CHATS FOUND!")
        return
    
    # Check messages from each authorized chat
    logger.info(f"\n2️⃣ Checking recent messages from {len(authorized_chats)} authorized chats...")
    
    for chat in authorized_chats:
        logger.info(f"\n🔍 Checking chat: {chat.id}")
        messages = whatsapp_client.get_messages(chat.id, limit=5)
        
        if not messages:
            logger.warning(f"⚠️ No messages found in {chat.id}")
            continue
        
        logger.info(f"📨 Found {len(messages)} messages:")
        current_time = time.time()
        
        for i, msg in enumerate(messages):
            try:
                from datetime import datetime
                msg_time = datetime.fromisoformat(msg.timestamp.replace('Z', '+00:00'))
                msg_timestamp = msg_time.timestamp()
                age_minutes = (current_time - msg_timestamp) / 60
                
                logger.info(f"   {i+1}. [{msg.id[:8]}...] From {msg.sender} ({age_minutes:.1f}m ago)")
                logger.info(f"      Text: '{msg.text}'")
                logger.info(f"      FromMe: {msg.is_from_me}")
                
                # Check if this message would be processed
                if msg.is_from_me:
                    logger.info(f"      ❌ SKIP: Own message")
                elif age_minutes > 2:
                    logger.info(f"      ❌ SKIP: Too old ({age_minutes:.1f}m > 2m)")
                elif msg_timestamp < (whatsapp_client._startup_time - 30):
                    logger.info(f"      ❌ SKIP: Before startup")
                else:
                    # Check if triggered
                    is_triggered = whatsapp_client.is_message_triggered(msg)
                    logger.info(f"      {'✅ WOULD PROCESS' if is_triggered else '❌ NOT TRIGGERED'}")
                    
            except Exception as e:
                logger.error(f"      ❌ Error parsing message: {e}")
    
    # Test get_new_messages directly
    logger.info(f"\n3️⃣ Testing get_new_messages() directly...")
    new_messages = whatsapp_client.get_new_messages()
    logger.info(f"📨 get_new_messages() returned: {len(new_messages)} messages")
    
    if new_messages:
        for msg in new_messages:
            logger.info(f"   NEW: '{msg.text}' from {msg.sender}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🔍 LIVE DEBUG COMPLETE")

if __name__ == "__main__":
    live_debug() 