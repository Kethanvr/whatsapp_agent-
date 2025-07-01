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
        
        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.config.get("model", "gemini-2.5-flash-lite-preview-06-17")
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
        """Process Q&A request using Gemini"""
        try:
            # Build the conversation context
            system_prompt = self._build_system_prompt()
            user_message = request.message
            
            # Generate response using Gemini
            full_prompt = f"{system_prompt}\n\nUser Question: {user_message}\n\nAssistant:"
            
            # Use asyncio to make the synchronous call non-blocking
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=self.temperature,
                        max_output_tokens=self.max_tokens,
                    )
                )
            )
            
            if response and response.text:
                return AgentResponse(
                    agent_id=self.agent_id,
                    response=response.text.strip(),
                    confidence=0.85,  # High confidence for general Q&A
                    success=True,
                    metadata={
                        "model": self.config.get("model"),
                        "temperature": self.temperature,
                        "tokens_used": len(response.text.split())
                    }
                )
            else:
                raise Exception("No response generated from Gemini")
                
        except Exception as e:
            logger.error(f"❌ QnA Agent error: {str(e)}")
            return self._create_error_response(str(e), request)
    
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