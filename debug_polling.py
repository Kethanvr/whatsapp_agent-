#!/usr/bin/env python3
"""
Debug Polling - Check why bot polling isn't picking up messages
"""

import sys
import os
import time
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.whatsapp_client import whatsapp_client
from config.settings import settings

def debug_polling_issue():
    """Debug why the bot isn't picking up messages"""
    logger.info("🔍 DEBUGGING POLLING ISSUE")
    logger.info("=" * 60)
    
    # Check basic connectivity
    logger.info("1️⃣ Testing bridge connection...")
    if whatsapp_client.health_check():
        logger.info("✅ Bridge health check: OK")
    else:
        logger.error("❌ Bridge health check: FAILED")
        return
    
    # Check chats
    logger.info("\n2️⃣ Testing chat retrieval...")
    chats = whatsapp_client.get_chats()
    logger.info(f"✅ Retrieved {len(chats)} chats")
    
    # Find authorized chat
    authorized_chat = None
    for chat in chats[:10]:  # Check first 10
        if "917483531255" in chat.id:
            authorized_chat = chat
            logger.info(f"🎯 Found authorized chat: {chat.id} - {chat.name}")
            break
    
    if not authorized_chat:
        logger.warning("⚠️ Authorized chat not found in first 10 chats")
        # Show first few chats
        logger.info("📋 First 5 chats:")
        for i, chat in enumerate(chats[:5]):
            logger.info(f"   {i+1}. {chat.id} - {chat.name}")
        return
    
    # Check messages from authorized chat
    logger.info(f"\n3️⃣ Checking messages from {authorized_chat.id}...")
    messages = whatsapp_client.get_messages(authorized_chat.id, limit=5)
    logger.info(f"✅ Retrieved {len(messages)} messages")
    
    if messages:
        logger.info("📨 Recent messages:")
        for i, msg in enumerate(messages):
            logger.info(f"   {i+1}. From {msg.sender}: '{msg.text}' at {msg.timestamp}")
            logger.info(f"      ID: {msg.id}, FromMe: {msg.is_from_me}")
    else:
        logger.warning("⚠️ No messages found in authorized chat")
    
    # Test bot's get_new_messages with debug info
    logger.info(f"\n4️⃣ Testing bot's get_new_messages() method...")
    logger.info(f"   Bot startup time: {whatsapp_client._startup_time}")
    logger.info(f"   Current time: {time.time()}")
    logger.info(f"   Time since startup: {time.time() - whatsapp_client._startup_time:.1f} seconds")
    
    # Override startup time temporarily for testing
    original_startup = whatsapp_client._startup_time
    whatsapp_client._startup_time = time.time() - 3600  # 1 hour ago to catch recent messages
    
    logger.info("   Temporarily setting startup time to 1 hour ago for testing...")
    new_messages = whatsapp_client.get_new_messages()
    logger.info(f"✅ get_new_messages() returned {len(new_messages)} messages")
    
    if new_messages:
        logger.info("📨 New messages found:")
        for i, msg in enumerate(new_messages):
            logger.info(f"   {i+1}. From {msg.sender}: '{msg.text[:50]}...'")
    else:
        logger.warning("⚠️ get_new_messages() returned no messages")
    
    # Restore original startup time
    whatsapp_client._startup_time = original_startup
    
    # Test authorization directly
    logger.info(f"\n5️⃣ Testing authorization...")
    logger.info(f"   Authorized numbers: {settings.authorized_number_list}")
    
    if messages:
        test_msg = messages[0]
        is_triggered = whatsapp_client.is_message_triggered(test_msg)
        logger.info(f"   Test message '{test_msg.text}' from {test_msg.sender}")
        logger.info(f"   ✅ Triggered: {is_triggered}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🔍 POLLING DEBUG COMPLETE")

if __name__ == "__main__":
    debug_polling_issue() 