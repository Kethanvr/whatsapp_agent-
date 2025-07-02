"""
Message Processor - Orchestrates WhatsApp polling and AI responses with Multi-Agent support
"""
import asyncio
import time
from typing import Dict, List, Optional, Set
from loguru import logger
from core.whatsapp_client import whatsapp_client, Message
from core.ai_agent import ai_agent
try:
    from agents.enhanced_orchestrator import EnhancedAgentOrchestrator
    ENHANCED_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    from agents.orchestrator import AgentOrchestrator
    ENHANCED_ORCHESTRATOR_AVAILABLE = False
from config.settings import settings
from datetime import datetime

class MessageProcessor:
    """Coordinates message polling, processing, and responding with multi-agent orchestration"""
    
    def __init__(self):
        self.is_running = False
        self.message_history: List[Dict] = []
        self.processed_message_ids: Set[str] = set()  # Track processed messages
        self.chat_sessions: Dict[str, str] = {}  # Persistent chat sessions
        
        # Initialize orchestrator and fallback
        try:
            if ENHANCED_ORCHESTRATOR_AVAILABLE:
                self.orchestrator = EnhancedAgentOrchestrator()
                logger.info("🚀 Enhanced multi-agent orchestrator initialized")
            else:
                self.orchestrator = AgentOrchestrator()
                logger.info("🎯 Standard multi-agent orchestrator initialized")
            self.use_orchestrator = True
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize orchestrator: {e}")
            self.orchestrator = None
            self.use_orchestrator = False
        
        # Create single event loop for async operations
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            logger.info("🔄 Event loop initialized")
        except Exception as e:
            logger.warning(f"⚠️ Event loop setup failed: {e}")
            self.loop = None
        
        self.stats = {
            "total_messages_processed": 0,
            "total_responses_sent": 0,
            "orchestrator_responses": 0,
            "fallback_responses": 0,
            "errors": 0,
            "duplicates_skipped": 0,
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
        
        # Initialize with current time - ignore all historical messages
        logger.info("⏳ Initializing message tracking - ignoring historical messages...")
        
        # Wait a few seconds to let the system stabilize and avoid old messages
        startup_delay = 5
        logger.info(f"⏳ Waiting {startup_delay} seconds before processing messages...")
        time.sleep(startup_delay)
        
        logger.info("🎯 Bot is now LIVE and ready to process NEW messages!")
        logger.info(f"📱 Send messages with triggers: {', '.join(settings.trigger_list)}")
        if settings.authorized_number_list:
            logger.info(f"🔒 Authorized numbers: {', '.join(settings.authorized_number_list)}")
        
        try:
            poll_count = 0
            while self.is_running:
                poll_count += 1
                if poll_count % 20 == 0:  # Every minute
                    logger.info(f"🔄 Bot active - polling for new messages... (Poll #{poll_count})")
                
                self._poll_and_process_messages()
                time.sleep(settings.mcp_poll_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopping WhatsApp AI Assistant...")
            self.is_running = False
        except Exception as e:
            logger.error("💥 Fatal error in message processor: {}", e)
            self.is_running = False
        finally:
            # Clean up event loop
            if self.loop:
                self.loop.close()
                
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
                # Skip if already processed
                if message.id in self.processed_message_ids:
                    logger.debug(f"⏭️ Skipping already processed message: {message.id}")
                    self.stats["duplicates_skipped"] += 1
                    continue
                
                self._process_single_message(message)
                
        except Exception as e:
            logger.error(f"Error during message polling: {e}")
            self.stats["errors"] += 1
    
    def _process_single_message(self, message: Message):
        """Process a single incoming message with detailed logging"""
        message_start_time = time.time()
        
        try:
            logger.info(f"📱 [STEP 1] Processing message from {message.sender}")
            logger.info(f"📱 [STEP 1] Message text: '{message.text}'")
            logger.info(f"📱 [STEP 1] Chat ID: {message.chat_id}")
            
            # Mark as processed immediately to prevent duplicates
            self.processed_message_ids.add(message.id)
            
            # Clean up old processed IDs (keep last 1000)
            if len(self.processed_message_ids) > 1000:
                old_ids = list(self.processed_message_ids)[:500]
                for old_id in old_ids:
                    self.processed_message_ids.remove(old_id)
            
            logger.info(f"📱 [STEP 2] Checking if message should trigger response...")
            
            # Check if message should trigger bot response
            if not whatsapp_client.is_message_triggered(message):
                logger.info(f"📱 [STEP 2] ❌ Message not triggered: {message.text[:50]}...")
                return
            
            logger.info(f"📱 [STEP 2] ✅ Message triggered! Extracting query...")
            
            # Extract query from message
            query = whatsapp_client.extract_query_from_message(message)
            
            if not query.strip():
                logger.warning("📱 [STEP 2] ❌ Empty query after trigger extraction")
                return
            
            logger.info(f"📱 [STEP 3] 🤖 Processing query: '{query}'")
            
            # Generate AI response using orchestrator or fallback
            ai_start_time = time.time()
            response = self._generate_response(query, message)
            ai_processing_time = time.time() - ai_start_time
            
            logger.info(f"📱 [STEP 4] ✅ AI response generated in {ai_processing_time:.2f}s")
            logger.info(f"📱 [STEP 4] Response: '{response[:100]}...'")
            
            logger.info(f"📱 [STEP 5] 📤 Sending response to WhatsApp...")
            
            # Send response back to WhatsApp
            send_start_time = time.time()
            success = whatsapp_client.send_message(message.chat_id, response)
            send_time = time.time() - send_start_time
            
            total_processing_time = time.time() - message_start_time
            
            logger.info(f"📱 [STEP 5] Send result: {'✅ SUCCESS' if success else '❌ FAILED'} in {send_time:.2f}s")
            logger.info(f"📱 [FINAL] Total processing time: {total_processing_time:.2f}s")
            
            # Log the interaction
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "message_id": message.id,
                "chat_id": message.chat_id,
                "sender": message.sender,
                "query": query,
                "response": response,
                "ai_processing_time": ai_processing_time,
                "send_time": send_time,
                "total_processing_time": total_processing_time,
                "success": success
            }
            
            self.message_history.append(interaction)
            
            # Update stats
            self.stats["total_messages_processed"] += 1
            if success:
                self.stats["total_responses_sent"] += 1
                logger.info(f"✅ [SUCCESS] Complete message flow finished in {total_processing_time:.2f}s")
            else:
                self.stats["errors"] += 1
                logger.error(f"❌ [ERROR] Message processing failed - response not sent")
            
            # Keep only last 100 interactions in memory
            if len(self.message_history) > 100:
                self.message_history = self.message_history[-100:]
                
        except Exception as e:
            total_time = time.time() - message_start_time
            logger.error(f"❌ [CRITICAL ERROR] Processing message {message.id} failed after {total_time:.2f}s: {e}")
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
    
    def _get_session_id(self, message: Message) -> str:
        """Get or create persistent session ID for chat"""
        chat_id = message.chat_id
        
        if chat_id not in self.chat_sessions:
            # Create persistent session for this chat
            self.chat_sessions[chat_id] = f"{chat_id}_session"
            
        return self.chat_sessions[chat_id]
    
    def _generate_response(self, query: str, message: Message) -> str:
        """Generate response using orchestrator or fallback with timeout protection"""
        max_processing_time = 15  # Maximum 15 seconds for AI processing
        
        try:
            if self.use_orchestrator and self.orchestrator and self.loop:
                # Use orchestrator for multi-agent processing with timeout
                session_id = self._get_session_id(message)
                
                logger.info(f"🤖 Starting orchestrator processing for: {query[:50]}...")
                start_time = time.time()
                
                try:
                    # Add timeout to prevent hanging
                    import asyncio
                    
                    # Create a timeout for the orchestrator processing
                    agent_response = self.loop.run_until_complete(
                        asyncio.wait_for(
                            self.orchestrator.process_message(query, session_id),
                            timeout=max_processing_time
                        )
                    )
                    
                    processing_time = time.time() - start_time
                    logger.info(f"⏱️ Orchestrator completed in {processing_time:.2f}s")
                    
                    if agent_response.success:
                        self.stats["orchestrator_responses"] += 1
                        logger.info(f"🎯 Orchestrator success - Agent: {agent_response.agent_id}")
                        return agent_response.response
                    else:
                        logger.warning(f"⚠️ Orchestrator failed: {agent_response.error}")
                        return self._fallback_response(query, message)
                        
                except asyncio.TimeoutError:
                    processing_time = time.time() - start_time
                    logger.error(f"⏰ Orchestrator TIMEOUT after {processing_time:.2f}s - using fallback")
                    return self._fallback_response(query, message)
                    
                except Exception as e:
                    processing_time = time.time() - start_time
                    logger.error(f"❌ Orchestrator execution error after {processing_time:.2f}s: {e}")
                    return self._fallback_response(query, message)
            else:
                # Use fallback agent directly
                logger.info("🔄 Using fallback AI agent (orchestrator disabled)")
                return self._fallback_response(query, message)
                
        except Exception as e:
            logger.error(f"❌ Response generation error: {e}")
            return self._fallback_response(query, message)
    
    def _fallback_response(self, query: str, message: Message) -> str:
        """Generate response using fallback AI agent with simple timeout protection"""
        try:
            self.stats["fallback_responses"] += 1
            logger.info(f"🔄 Starting fallback AI processing for: {query[:50]}...")
            start_time = time.time()
            
            # Use a simple approach - just try with AI agent
            response = ai_agent.process_message(
                query=query,
                chat_id=message.chat_id,
                sender=message.sender
            )
            
            processing_time = time.time() - start_time
            logger.info(f"⏱️ Fallback AI completed in {processing_time:.2f}s")
            
            if response and response.strip():
                return response.strip()
            else:
                logger.warning("Empty response from fallback AI")
                return "Hi! I'm your AI assistant. How can I help you today?"
                
        except Exception as e:
            logger.error(f"❌ Fallback response error: {e}")
            return "Hi! I'm your AI assistant. I'm ready to help you!"
    
    async def process_web_message(self, query: str, session_id: str) -> Dict:
        """Process message from web dashboard"""
        try:
            if self.use_orchestrator and self.orchestrator:
                response = await self.orchestrator.process_message(query, session_id)
                return {
                    "success": response.success,
                    "response": response.response,
                    "agent_id": response.agent_id,
                    "confidence": response.confidence,
                    "error": response.error
                }
            else:
                # Fallback for web
                ai_response = ai_agent.process_message(
                    query=query,
                    chat_id="web_dashboard",
                    sender="dashboard_user"
                )
                return {
                    "success": True,
                    "response": ai_response,
                    "agent_id": "fallback_ai",
                    "confidence": 0.8,
                    "error": None
                }
                
        except Exception as e:
            logger.error(f"Web message processing error: {e}")
            return {
                "success": False,
                "response": "Error processing your request.",
                "agent_id": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def test_ai_response(self, query: str) -> str:
        """Test AI response without WhatsApp (for debugging)"""
        try:
            if self.use_orchestrator and self.orchestrator and self.loop:
                session_id = f"test_{int(time.time())}"
                response = self.loop.run_until_complete(
                    self.orchestrator.process_message(query, session_id)
                )
                return response.response if response.success else f"Error: {response.error}"
            else:
                return ai_agent.process_message(
                    query=query,
                    chat_id="test_chat",
                    sender="test_user"
                )
        except Exception as e:
            return f"Test error: {str(e)}"
    
    def get_agent_info(self) -> Dict:
        """Get information about available agents"""
        if self.use_orchestrator and self.orchestrator:
            return {
                "orchestrator_enabled": True,
                "agents": self.orchestrator.get_agent_info(),
                "total_agents": len(self.orchestrator.agents)
            }
        else:
            return {
                "orchestrator_enabled": False,
                "agents": [{"id": "fallback", "name": "Fallback AI Agent", "status": "active"}],
                "total_agents": 1
            }

# Global message processor instance
message_processor = MessageProcessor() 