"""
Message Processor - Orchestrates WhatsApp polling and AI responses with Multi-Agent support
"""
import asyncio
import time
from typing import Dict, List, Optional
from loguru import logger
from core.whatsapp_client import whatsapp_client, Message
from core.ai_agent import ai_agent
from agents.orchestrator import AgentOrchestrator
from config.settings import settings
from datetime import datetime

class MessageProcessor:
    """Coordinates message polling, processing, and responding with multi-agent orchestration"""
    
    def __init__(self):
        self.is_running = False
        self.message_history: List[Dict] = []
        
        # Initialize orchestrator and fallback
        try:
            self.orchestrator = AgentOrchestrator()
            self.use_orchestrator = True
            logger.info("🎯 Multi-agent orchestrator initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize orchestrator: {e}")
            self.orchestrator = None
            self.use_orchestrator = False
        
        self.stats = {
            "total_messages_processed": 0,
            "total_responses_sent": 0,
            "orchestrator_responses": 0,
            "fallback_responses": 0,
            "errors": 0,
            "start_time": None
        }
    
    def start_polling(self):
        """Start the main message polling loop"""
        logger.info("🚀 Starting WhatsApp AI Assistant...")
        
        # Check MCP server connectivity
        if not whatsapp_client.health_check():
            logger.error("❌ Cannot connect to WhatsApp MCP server. Please ensure it's running on {}", 
                        settings.mcp_server_url)
            return False
        
        logger.info("✅ Connected to WhatsApp MCP server")
        
        self.is_running = True
        self.stats["start_time"] = datetime.now()
        
        try:
            while self.is_running:
                self._poll_and_process_messages()
                time.sleep(settings.mcp_poll_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopping WhatsApp AI Assistant...")
            self.is_running = False
        except Exception as e:
            logger.error("💥 Fatal error in message processor: {}", e)
            self.is_running = False
            
        return True
    
    def stop_polling(self):
        """Stop the polling loop"""
        self.is_running = False
        logger.info("🛑 Message polling stopped")
    
    def _poll_and_process_messages(self):
        """Poll for new messages and process them"""
        try:
            new_messages = whatsapp_client.get_new_messages()
            
            if not new_messages:
                return
            
            logger.info(f"📨 Found {len(new_messages)} new message(s)")
            
            for message in new_messages:
                self._process_single_message(message)
                
        except Exception as e:
            logger.error(f"Error during message polling: {e}")
            self.stats["errors"] += 1
    
    def _process_single_message(self, message: Message):
        """Process a single incoming message"""
        try:
            logger.info(f"📱 Processing message from {message.sender} in chat {message.chat_id}")
            
            # Check if message should trigger bot response
            if not whatsapp_client.is_message_triggered(message):
                logger.debug(f"Message not triggered: {message.text[:50]}...")
                return
            
            # Extract query from message
            query = whatsapp_client.extract_query_from_message(message)
            
            if not query.strip():
                logger.warning("Empty query after trigger extraction")
                return
            
            logger.info(f"🤖 Processing query: {query[:100]}...")
            
            # Generate AI response using orchestrator or fallback
            start_time = time.time()
            response = self._generate_response(query, message)
            processing_time = time.time() - start_time
            
            # Send response back to WhatsApp
            success = whatsapp_client.send_message(message.chat_id, response)
            
            # Log the interaction
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "message_id": message.id,
                "chat_id": message.chat_id,
                "sender": message.sender,
                "query": query,
                "response": response,
                "processing_time": processing_time,
                "success": success
            }
            
            self.message_history.append(interaction)
            
            # Update stats
            self.stats["total_messages_processed"] += 1
            if success:
                self.stats["total_responses_sent"] += 1
                logger.success(f"✅ Response sent successfully in {processing_time:.2f}s")
            else:
                self.stats["errors"] += 1
                logger.error("❌ Failed to send response")
            
            # Keep only last 100 interactions in memory
            if len(self.message_history) > 100:
                self.message_history = self.message_history[-100:]
                
        except Exception as e:
            logger.error(f"Error processing message {message.id}: {e}")
            self.stats["errors"] += 1
    
    def get_recent_interactions(self, limit: int = 10) -> List[Dict]:
        """Get recent message interactions for dashboard"""
        return self.message_history[-limit:] if self.message_history else []
    
    def get_stats(self) -> Dict:
        """Get processing statistics"""
        stats = self.stats.copy()
        if stats["start_time"]:
            stats["uptime_seconds"] = (datetime.now() - stats["start_time"]).total_seconds()
        return stats
    
    def _generate_response(self, query: str, message: Message) -> str:
        """Generate response using orchestrator or fallback"""
        try:
            if self.use_orchestrator and self.orchestrator:
                # Use orchestrator for multi-agent processing
                session_id = f"{message.chat_id}_{int(time.time())}"
                
                # Run async orchestrator in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    agent_response = loop.run_until_complete(
                        self.orchestrator.process_message(query, session_id)
                    )
                    
                    if agent_response.success:
                        self.stats["orchestrator_responses"] += 1
                        logger.info(f"🎯 Orchestrator success - Agent: {agent_response.agent_id}")
                        return agent_response.response
                    else:
                        logger.warning(f"⚠️ Orchestrator failed: {agent_response.error}")
                        return self._fallback_response(query, message)
                        
                finally:
                    loop.close()
            else:
                # Use fallback agent
                return self._fallback_response(query, message)
                
        except Exception as e:
            logger.error(f"❌ Response generation error: {e}")
            return self._fallback_response(query, message)
    
    def _fallback_response(self, query: str, message: Message) -> str:
        """Generate response using fallback AI agent"""
        try:
            self.stats["fallback_responses"] += 1
            logger.info("🔄 Using fallback AI agent")
            
            response = ai_agent.process_message(
                query=query,
                sender=message.sender,
                chat_id=message.chat_id
            )
            return response
            
        except Exception as e:
            logger.error(f"❌ Fallback agent error: {e}")
            return "Sorry, I'm experiencing technical difficulties. Please try again later."
    
    async def process_web_message(self, query: str, session_id: str) -> Dict:
        """Process message from web interface (for Streamlit dashboard)"""
        try:
            if self.use_orchestrator and self.orchestrator:
                response = await self.orchestrator.process_message(query, session_id)
                
                return {
                    "success": response.success,
                    "response": response.response,
                    "agent_id": response.agent_id,
                    "confidence": response.confidence,
                    "metadata": response.metadata or {}
                }
            else:
                # Fallback to original agent
                response_text = ai_agent.get_simple_response(query, "Web User")
                return {
                    "success": bool(response_text),
                    "response": response_text or "Sorry, I couldn't process your request.",
                    "agent_id": "fallback-agent",
                    "confidence": 0.5,
                    "metadata": {}
                }
                
        except Exception as e:
            logger.error(f"❌ Web message processing error: {e}")
            return {
                "success": False,
                "response": "Sorry, I'm experiencing technical difficulties.",
                "agent_id": "error",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }

    def test_ai_response(self, query: str) -> str:
        """Test AI response generation (for dashboard)"""
        try:
            if self.use_orchestrator and self.orchestrator:
                # Test with orchestrator
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    response = loop.run_until_complete(
                        self.orchestrator.process_message(query, "test_session")
                    )
                    return response.response if response.success else f"Error: {response.error}"
                finally:
                    loop.close()
            else:
                # Test with fallback
                return ai_agent.get_simple_response(query, "Test User")
        except Exception as e:
            logger.error(f"Test response failed: {e}")
            return f"Error: {str(e)}"
    
    def get_agent_info(self) -> Dict:
        """Get information about available agents"""
        if self.orchestrator:
            return {
                "orchestrator_enabled": self.use_orchestrator,
                "agents": self.orchestrator.get_agent_info() if hasattr(self.orchestrator, 'get_agent_info') else [],
                "fallback_available": True
            }
        return {
            "orchestrator_enabled": False,
            "agents": [],
            "fallback_available": True
        }

# Global processor instance
message_processor = MessageProcessor() 