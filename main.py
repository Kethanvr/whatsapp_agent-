#!/usr/bin/env python3
"""
WhatsApp AI Assistant - Main Entry Point
Powered by Gemini + LangChain + LangGraph + WhatsApp-MCP
"""

import os
import sys
import signal
from loguru import logger
from core.message_processor import message_processor
from config.settings import settings

def setup_logging():
    """Configure logging with loguru"""
    # Remove default logger
    logger.remove()
    
    # Console logging
    if settings.enable_console_logs:
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.log_level,
            colorize=True
        )
    
    # File logging
    if settings.enable_file_logs:
        logger.add(
            "logs/whatsapp_ai_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=settings.log_level
        )

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    message_processor.stop_polling()
    sys.exit(0)

def check_environment():
    """Check if environment is properly configured"""
    issues = []
    
    # Check for required API key
    if not settings.gemini_api_key or settings.gemini_api_key == "your-google-gemini-api-key-here":
        issues.append("❌ GEMINI_API_KEY not configured in .env file")
    
    # Check MCP server URL format
    if not settings.mcp_server_url.startswith(('http://', 'https://')):
        issues.append("❌ MCP_SERVER_URL must start with http:// or https://")
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    if issues:
        logger.error("Environment configuration issues found:")
        for issue in issues:
            logger.error(issue)
        logger.error("Please fix these issues before starting the assistant.")
        return False
    
    return True

def display_startup_info():
    """Display startup information"""
    logger.info("🤖 WhatsApp AI Assistant Starting...")
    logger.info("=" * 50)
    logger.info(f"Bot Name: {settings.bot_name}")
    logger.info(f"Agent Model: {settings.agent_model}")
    logger.info(f"MCP Server: {settings.mcp_server_url}")
    logger.info(f"Poll Interval: {settings.mcp_poll_interval}s")
    logger.info(f"Triggers: {', '.join(settings.trigger_list)}")
    logger.info(f"Group Chats: {'Enabled' if settings.enable_group_chats else 'Disabled'}")
    logger.info(f"Personal Chats: {'Enabled' if settings.enable_personal_chats else 'Disabled'}")
    
    if settings.authorized_number_list:
        logger.info(f"Authorized Numbers: {len(settings.authorized_number_list)} configured")
    else:
        logger.info("Authorized Numbers: All numbers allowed")
    
    logger.info("=" * 50)
    logger.info("💡 Dashboard available at: http://localhost:8501")
    logger.info("💡 To start dashboard: streamlit run dashboard/streamlit_app.py")
    logger.info("=" * 50)

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Display startup info
    display_startup_info()
    
    try:
        # Start the message processor
        success = message_processor.start_polling()
        
        if not success:
            logger.error("Failed to start message processor")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 WhatsApp AI Assistant stopped")

if __name__ == "__main__":
    main() 