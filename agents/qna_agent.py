"""
Q&A Agent

Specialized agent for handling general questions and conversational AI
using Google Gemini for natural language understanding and generation.
"""

import asyncio
from typing import Dict, Any
import google.generativeai as genai
from config.settings import settings
from .base_agent import BaseAgent, AgentRequest, AgentResponse
import logging

logger = logging.getLogger(__name__)

class QnAAgent(BaseAgent):
    """
    Question & Answer Agent using Google Gemini
    
    Handles:
    - General questions and explanations  
    - Factual queries
    - Definitions and clarifications
    - Conversational interactions
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        super().__init__(agent_config)
        
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        
        # Initialize the model with thinking disabled
        model_name = self.config.get("model", "gemini-2.0-flash")
        
        # Safety settings to prevent blocks
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # System instruction to disable thinking mode
        system_instruction = "You are a helpful AI assistant. Respond directly without showing your thinking process or reasoning steps."
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            safety_settings=safety_settings,
            system_instruction=system_instruction
        )
        
        # Agent-specific configuration
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 500)
        
        # Keywords for routing decisions
        self.keywords = [
            "what", "how", "why", "explain", "define", "tell me", "help",
            "question", "answer", "ask", "info", "information", "describe",
            "meaning", "examples", "difference", "compare", "clarify"
        ]
        
        logger.info(f"🧠 {self.name} initialized with Gemini model")
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process Q&A request using Gemini with improved error handling"""
        try:
            user_message = request.message.strip()
            
            if not user_message:
                raise Exception("Empty message received")
            
            logger.info(f"🤖 Processing: {user_message[:50]}...")
            
            # Create generation config with thinking disabled
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                candidate_count=1,
                top_p=0.9,
                top_k=40,
                # Disable thinking mode for 2.0+ models
                response_schema=None,
                response_mime_type="text/plain"
            )
            
            # Use asyncio to make the synchronous call non-blocking
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self._generate_content_safe(user_message, generation_config)
            )
            
            if response and hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
                
                logger.info(f"✅ Generated response: {response_text[:50]}...")
                
                return AgentResponse(
                    agent_id=self.agent_id,
                    response=response_text,
                    confidence=0.85,
                    success=True,
                    metadata={
                        "model": self.model.model_name,
                        "temperature": self.temperature,
                        "response_length": len(response_text),
                        "tokens_used": len(response_text.split())
                    }
                )
            else:
                logger.warning("⚠️ Empty response from Gemini")
                raise Exception("Empty response generated from Gemini")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ QnA Agent error: {error_msg}")
            
            # Create a more helpful error response
            fallback_response = self._get_fallback_response(request.message)
            
            return AgentResponse(
                agent_id=self.agent_id,
                response=fallback_response,
                confidence=0.1,
                success=False,
                error=error_msg,
                metadata={"fallback_used": True}
            )
    
    def _generate_content_safe(self, message: str, generation_config):
        """Safely generate content with proper error handling"""
        try:
            # Simple prompt without complex formatting
            prompt = f"Please answer this question clearly and helpfully: {message}"
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Check for safety blocks
            if hasattr(response, 'prompt_feedback'):
                if response.prompt_feedback.block_reason:
                    logger.warning(f"⚠️ Prompt blocked: {response.prompt_feedback.block_reason}")
                    raise Exception(f"Content blocked: {response.prompt_feedback.block_reason}")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Gemini API error: {str(e)}")
            raise e
    
    def _get_fallback_response(self, message: str) -> str:
        """Generate a fallback response when Gemini fails"""
        message_lower = message.lower()
        
        if any(greet in message_lower for greet in ["hello", "hi", "hey"]):
            return "Hello! I'm having some technical difficulties right now, but I'm here to help. Please try asking your question again."
        
        if "?" in message:
            return "I'm sorry, I'm experiencing some technical issues and can't process your question right now. Please try again in a moment."
        
        return "I apologize, but I'm having technical difficulties at the moment. Please try your request again."
    
    def can_handle(self, message: str) -> float:
        """
        Determine confidence for handling this message
        
        Returns higher confidence for:
        - Questions (what, how, why, etc.)
        - Requests for explanations
        - General conversational queries
        """
        message_lower = message.lower()
        
        # Check for question keywords
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message_lower)
        
        # Check for question marks
        has_question_mark = "?" in message
        
        # Check for conversational patterns
        is_greeting = any(greet in message_lower for greet in ["hello", "hi", "hey", "good morning", "good evening"])
        is_request = any(req in message_lower for req in ["please", "can you", "could you", "would you"])
        
        # Calculate confidence score
        confidence = 0.3  # Base confidence for any message
        
        if keyword_matches > 0:
            confidence += min(keyword_matches * 0.2, 0.4)  # Up to 0.4 for keyword matches
            
        if has_question_mark:
            confidence += 0.2
            
        if is_greeting or is_request:
            confidence += 0.1
            
        # Cap at 0.9 (leave room for more specialized agents)
        return min(confidence, 0.9)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the Q&A agent"""
        return f"""You are {self.name}, a helpful AI assistant specialized in answering questions and providing explanations.

Your role:
- Answer questions clearly and accurately
- Provide helpful explanations and definitions
- Be conversational and friendly
- Keep responses concise but informative
- If you're unsure about something, say so

Guidelines:
- Maximum response length: {self.max_tokens} tokens
- Be helpful, harmless, and honest
- Use simple language when possible
- Provide examples when helpful

Current capabilities: {', '.join(self.capabilities)}""" 