#!/usr/bin/env python3
"""
WhatsApp AI Assistant - Main Entry Point
Powered by Gemini + LangChain + LangGraph + WhatsApp-MCP
"""

import os
import sys
import signal
import argparse
from loguru import logger
from core.message_processor import message_processor
from config.settings import settings

def setup_logging():
    """Configure clean, structured logging with loguru"""
    # Remove default logger
    logger.remove()
    
    # Console logging with cleaner format
    if settings.enable_console_logs:
        # Main console format - cleaner and more readable
        logger.add(
            sys.stdout,
            format="<blue>{time:HH:mm:ss}</blue> | <level>{level:^8}</level> | <level>{message}</level>",
            level=settings.log_level,
            colorize=True,
            filter=lambda record: not record["name"].startswith("core.whatsapp_client") or record["level"].name in ["ERROR", "WARNING"]
        )
        
        # Separate detailed logger for debugging (only for DEBUG level)
        if settings.log_level == "DEBUG":
            logger.add(
                sys.stdout, 
                format="<green>{time:HH:mm:ss}</green> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
                level="DEBUG",
                colorize=True,
                filter=lambda record: record["level"].name == "DEBUG"
            )
    
    # File logging with full details
    if settings.enable_file_logs:
        logger.add(
            "logs/whatsapp_ai_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="7 days",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG"  # Always log everything to file
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
    """Display clean startup information"""
    # Main header
    logger.info("🚀 Starting WhatsApp AI Assistant with Multi-Agent Orchestration")
    logger.info("")
    
    # Configuration section
    logger.info("⚙️  System Configuration:")
    logger.info(f"   • Bot Name: {settings.bot_name}")
    logger.info(f"   • Agent Model: {settings.agent_model}")
    logger.info(f"   • MCP Server: {settings.mcp_server_url}")
    logger.info(f"   • Poll Interval: {settings.mcp_poll_interval}s")
    logger.info("")
    
    # Bot behavior section  
    logger.info("🤖 Bot Behavior:")
    logger.info(f"   • Triggers: {', '.join(settings.trigger_list)}")
    logger.info(f"   • Group Chats: {'✅ Enabled' if settings.enable_group_chats else '❌ Disabled'}")
    logger.info(f"   • Personal Chats: {'✅ Enabled' if settings.enable_personal_chats else '❌ Disabled'}")
    
    if settings.authorized_number_list:
        logger.info(f"   • Authorization: 🔒 {len(settings.authorized_number_list)} numbers allowed")
    else:
        logger.info("   • Authorization: 🌐 All numbers allowed")
    logger.info("")
    
    # Access information
    logger.info("🌐 Access Points:")
    logger.info("   • Dashboard: http://localhost:8503")
    logger.info("   • Start Command: python run_dashboard.py")
    logger.info("")
    
    # Status indicator
    logger.info("🎯 Multi-Agent System: Initializing...")
    logger.info("📱 WhatsApp Bridge: Connecting...")
    logger.info("")

def display_status_update(message: str, status: str = "INFO"):
    """Display clean status updates"""
    icons = {
        "SUCCESS": "✅",
        "ERROR": "❌", 
        "WARNING": "⚠️",
        "INFO": "ℹ️",
        "LOADING": "⏳"
    }
    
    icon = icons.get(status, "ℹ️")
    if status == "SUCCESS":
        logger.success(f"{icon} {message}")
    elif status == "ERROR":
        logger.error(f"{icon} {message}")
    elif status == "WARNING":
        logger.warning(f"{icon} {message}")
    else:
        logger.info(f"{icon} {message}")

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=int(os.environ.get('PORT', 3333)), help='Port to bind HTTP server (if applicable)')
    args = parser.parse_args()
    # The port is available as args.port, use it if you add an HTTP server in the future.
    # Setup logging
    setup_logging()
    
    # Display startup info
    display_startup_info()
    
    # Check environment
    if not check_environment():
        display_status_update("Environment configuration failed", "ERROR")
        sys.exit(1)
    
    display_status_update("Environment configuration valid", "SUCCESS")
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    display_status_update("Signal handlers configured", "SUCCESS")
    
    try:
        # Initialize multi-agent system
        display_status_update("Initializing multi-agent orchestrator...", "LOADING")
        
        # Start the message processor
        display_status_update("Starting message processor...", "LOADING")
        success = message_processor.start_polling()
        
        if not success:
            display_status_update("Message processor failed to start", "ERROR")
            sys.exit(1)
        
        display_status_update("System is now ready and processing messages!", "SUCCESS")
            
    except KeyboardInterrupt:
        logger.info("")
        display_status_update("Shutdown requested by user", "INFO")
    except Exception as e:
        display_status_update(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)
    finally:
        display_status_update("WhatsApp AI Assistant stopped", "INFO")
        logger.info("")

if __name__ == "__main__":
    main() 