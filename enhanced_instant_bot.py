"""
Enhanced Instant WhatsApp Bot with Perfect Timing & Multimedia Support
- Only processes messages sent AFTER bot starts (no old messages)
- No duplicate responses 
- Real-time processing
- Multimedia support (images, documents, etc.)
- Enhanced orchestrator with sub-agents
"""

import asyncio
import time
from datetime import datetime
from loguru import logger
from core.whatsapp_client import whatsapp_client
from core.message_processor import message_processor, ENHANCED_ORCHESTRATOR_AVAILABLE

def main():
    """Enhanced instant bot with perfect timing and multimedia support"""
    logger.info("⚡ ENHANCED INSTANT BOT - Starting with multimedia support...")
    
    # Reset everything - ONLY process messages sent AFTER bot starts
    whatsapp_client._last_message_ids.clear()
    whatsapp_client._startup_time = time.time()  # NOW - only process future messages
    message_processor.processed_message_ids.clear()
    
    # Mark ALL existing messages as "seen" to avoid processing old ones
    logger.info("🔄 Marking all existing messages as seen to avoid old message processing...")
    try:
        chats = whatsapp_client.get_chats()
        seen_count = 0
        
        for chat in chats[:15]:  # Check top 15 chats
            try:
                messages = whatsapp_client.get_messages(chat.id, limit=5)
                if messages:
                    # Mark the latest message as seen
                    whatsapp_client._last_message_ids[chat.id] = messages[0].id
                    seen_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Error marking chat {chat.id}: {e}")
                continue
        
        logger.info(f"✅ Marked {seen_count} chats as seen - will ignore all existing messages")
        
    except Exception as e:
        logger.error(f"❌ Error during message marking: {e}")
    
    logger.info("🔧 All tracking reset, startup time set to NOW")
    logger.info("⚡ Processing ONLY NEW messages sent after this moment...")
    
    # Show enhanced capabilities
    if ENHANCED_ORCHESTRATOR_AVAILABLE:
        logger.info("🚀 Enhanced Orchestrator ACTIVE with capabilities:")
        logger.info("  🎨 Image Understanding & Generation")
        logger.info("  🔍 Real-time Web Search")
        logger.info("  📝 OCR & Text Extraction")
        logger.info("  🧠 Multi-Agent Coordination")
        logger.info("  🔄 Agent-to-Agent Communication")
    else:
        logger.info("🔄 Standard orchestrator active")
    
    logger.info(f"📱 Send messages with triggers: {', '.join(['!ask', '@ai', '@bot', '>'])}")
    logger.info(f"🔒 Authorized numbers: {', '.join(['+917483531255', '+916360751048'])}")
    logger.info("🎯 Bot is now LIVE and ready for NEW messages!")
    
    # Start processing with enhanced timing
    poll_count = 0
    last_status_log = time.time()
    
    try:
        while True:
            poll_count += 1
            current_time = time.time()
            
            # Status logging every 30 seconds
            if current_time - last_status_log >= 30:
                logger.info(f"⚡ Enhanced bot ACTIVE - Poll #{poll_count} | {datetime.now().strftime('%H:%M:%S')}")
                last_status_log = current_time
                
                # Show stats
                stats = message_processor.get_stats()
                if stats.get("total_messages_processed", 0) > 0:
                    logger.info(f"📊 Processed: {stats['total_messages_processed']} | "
                              f"Responses: {stats['total_responses_sent']} | "
                              f"Errors: {stats['errors']}")
            
            # Process new messages ONLY
            try:
                new_messages = whatsapp_client.get_new_messages()
                
                if new_messages:
                    logger.info(f"📨 Found {len(new_messages)} NEW message(s)")
                    
                    for message in new_messages:
                        # Skip if already processed (duplicate prevention)
                        if message.id in message_processor.processed_message_ids:
                            logger.debug(f"⏭️ Skipping duplicate message: {message.id}")
                            continue
                        
                        # Enhanced message processing with multimedia
                        logger.info(f"⚡ Processing NEW message from {message.sender}: '{message.text[:50]}...'")
                        
                        # Process immediately
                        message_processor._process_single_message(message)
                        
                        # Mark as processed to prevent duplicates
                        message_processor.processed_message_ids.add(message.id)
                
            except Exception as e:
                logger.error(f"❌ Error processing messages: {e}")
            
            # Short polling interval for instant responses
            time.sleep(2)  # 2-second polling for instant responses
            
    except KeyboardInterrupt:
        logger.info("🛑 Enhanced instant bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error in enhanced instant bot: {e}")
    
    logger.info("👋 Enhanced instant bot shutdown complete")

if __name__ == "__main__":
    main()