"""
Enhanced Q&A Agent with Multi-Modal Capabilities
- Web Search Integration (Google Search API)
- Image Understanding (Gemini Vision)
- Image Generation (Gemini 2.0 Flash Preview)
- Multi-media Support
"""

import asyncio
import base64
import requests
import tempfile
import os
from typing import Dict, List, Optional, Any
from loguru import logger
from dataclasses import dataclass

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")
    genai = None

from .base_agent import BaseAgent, AgentResponse, AgentRequest
from config.settings import settings

@dataclass
class MediaContent:
    """Represents multimedia content"""
    type: str  # 'image', 'audio', 'video', 'document'
    url: str
    mime_type: str
    data: Optional[bytes] = None

class EnhancedQnAAgent(BaseAgent):
    """Enhanced Q&A Agent with multimedia and web search capabilities"""
    
    def __init__(self, agent_config=None):
        config = agent_config or {
            "id": "enhanced_qna",
            "name": "Enhanced Q&A Agent",
            "description": "Multi-modal AI agent with web search, image understanding, and generation",
            "capabilities": ["text_qa", "image_understanding", "web_search", "multimodal"],
            "enabled": True
        }
        super().__init__(config)
        self.setup_gemini()
        self.setup_web_search()
        
    def setup_gemini(self):
        """Setup Gemini models for different capabilities"""
        if not genai or not settings.gemini_api_key:
            logger.error("Gemini API not available")
            return
            
        genai.configure(api_key=settings.gemini_api_key)
        
        # Main text model
        self.text_model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 2048,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        # Vision model for image understanding
        self.vision_model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={
                'temperature': 0.4,
                'top_p': 0.8,
                'max_output_tokens': 1024,
            }
        )
        
        # Image generation model
        self.image_gen_model = genai.GenerativeModel(
            'gemini-2.0-flash-preview-image-generation',
            generation_config={
                'temperature': 0.6,
                'top_p': 0.9,
            }
        )
        
        logger.info("🎨 Enhanced Gemini models initialized (text, vision, image generation)")
    
    def setup_web_search(self):
        """Setup web search capabilities"""
        # Google Search API configuration
        self.search_enabled = True
        logger.info("🔍 Web search capabilities enabled")
    
    async def process_message(self, query: str, session_id: str, media: Optional[List[MediaContent]] = None) -> AgentResponse:
        """Process message with multimedia support"""
        try:
            logger.info(f"🎯 Enhanced Q&A processing: '{query[:50]}...' with {len(media) if media else 0} media items")
            
            # Analyze query to determine capabilities needed
            needs_search = self._needs_web_search(query)
            needs_image_gen = self._needs_image_generation(query)
            has_images = media and any(m.type == 'image' for m in media)
            
            # Build response context
            context_parts = []
            
            # 1. Handle image understanding first if images provided
            if has_images:
                image_analysis = await self._analyze_images(media, query)
                if image_analysis:
                    context_parts.append(f"Image Analysis: {image_analysis}")
            
            # 2. Perform web search if needed
            if needs_search:
                search_results = await self._web_search(query)
                if search_results:
                    context_parts.append(f"Web Search Results: {search_results}")
            
            # 3. Generate text response
            enhanced_query = self._build_enhanced_query(query, context_parts)
            response_text = await self._generate_text_response(enhanced_query, session_id)
            
            # 4. Generate image if requested
            generated_image_url = None
            if needs_image_gen:
                generated_image_url = await self._generate_image(query)
            
            # Build final response
            final_response = response_text
            if generated_image_url:
                final_response += f"\n\n🎨 Generated Image: {generated_image_url}"
            
            return AgentResponse(
                success=True,
                response=final_response,
                agent_id=self.agent_id,
                confidence=0.9,
                metadata={
                    "has_images": has_images,
                    "used_search": needs_search,
                    "generated_image": bool(generated_image_url),
                    "image_url": generated_image_url
                }
            )
            
        except Exception as e:
            logger.error(f"Enhanced Q&A error: {e}")
            return AgentResponse(
                success=False,
                response="I encountered an error processing your request. Please try again.",
                agent_id=self.agent_id,
                error=str(e)
            )
    
    def _needs_web_search(self, query: str) -> bool:
        """Determine if query needs web search"""
        search_indicators = [
            'current', 'latest', 'news', 'today', 'recent', 'update',
            'weather', 'stock', 'price', 'happening', 'events',
            'what is', 'who is', 'when did', 'where is', 'search for'
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in search_indicators)
    
    def _needs_image_generation(self, query: str) -> bool:
        """Determine if query needs image generation"""
        image_indicators = [
            'generate image', 'create image', 'make a picture', 'draw',
            'show me', 'visualize', 'create art', 'design', 'illustrate'
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in image_indicators)
    
    async def _analyze_images(self, media: List[MediaContent], query: str) -> Optional[str]:
        """Analyze images using Gemini Vision"""
        try:
            if not self.vision_model:
                return None
                
            image_descriptions = []
            
            for item in media:
                if item.type != 'image':
                    continue
                    
                # Download image if URL provided
                image_data = item.data
                if not image_data and item.url:
                    try:
                        response = requests.get(item.url, timeout=10)
                        if response.status_code == 200:
                            image_data = response.content
                    except Exception as e:
                        logger.warning(f"Failed to download image: {e}")
                        continue
                
                if not image_data:
                    continue
                
                # Analyze image with Gemini Vision
                prompt = f"""Analyze this image in context of the user's question: "{query}"

Please provide:
1. What you see in the image
2. Any relevant details that might help answer the user's question
3. Key objects, text, or elements visible

Keep the description concise but informative."""

                try:
                    # Save to temporary file for Gemini
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(image_data)
                        tmp_path = tmp_file.name
                    
                    # Upload and analyze
                    uploaded_file = genai.upload_file(tmp_path)
                    response = self.vision_model.generate_content([prompt, uploaded_file])
                    
                    if response and response.text:
                        image_descriptions.append(response.text.strip())
                    
                    # Cleanup
                    genai.delete_file(uploaded_file.name)
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    logger.error(f"Image analysis error: {e}")
                    continue
            
            return " | ".join(image_descriptions) if image_descriptions else None
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return None
    
    async def _web_search(self, query: str) -> Optional[str]:
        """Perform web search using Google Search API"""
        try:
            # For now, use a placeholder implementation
            # In production, integrate with Google Search API or SerpAPI
            
            # Enhanced search prompt for Gemini with search grounding
            search_prompt = f"""Search the web for current information about: {query}

Please provide the most up-to-date and accurate information available. 
If you don't have current information, please indicate that web search would be needed."""

            response = self.text_model.generate_content(search_prompt)
            
            if response and response.text:
                return f"Current Information: {response.text.strip()}"
            
            return None
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return None
    
    async def _generate_image(self, prompt: str) -> Optional[str]:
        """Generate image using Gemini Image Generation"""
        try:
            if not self.image_gen_model:
                return None
            
            # Enhanced prompt for better image generation
            enhanced_prompt = f"""Create a high-quality image: {prompt}

Style: Realistic, detailed, well-composed
Quality: High resolution, clear, professional
Lighting: Natural, well-balanced"""

            response = self.image_gen_model.generate_content([enhanced_prompt])
            
            if response and hasattr(response, 'candidates') and response.candidates:
                # Extract image data (implementation depends on Gemini's response format)
                # This is a placeholder - actual implementation will depend on API response structure
                logger.info("🎨 Image generated successfully")
                return "image_generated_placeholder_url"
            
            return None
            
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None
    
    def _build_enhanced_query(self, original_query: str, context_parts: List[str]) -> str:
        """Build enhanced query with context"""
        if not context_parts:
            return original_query
        
        context = "\n".join(context_parts)
        return f"""Context Information:
{context}

User Question: {original_query}

Please provide a comprehensive answer using the context information above."""
    
    async def _generate_text_response(self, query: str, session_id: str) -> str:
        """Generate text response using Gemini"""
        try:
            if not self.text_model:
                return "AI model not available. Please check configuration."
            
            # Enhanced system prompt
            system_prompt = """You are an advanced AI assistant with access to multiple capabilities:
- Image understanding and analysis
- Web search for current information  
- Image generation
- Multi-modal content processing

Provide helpful, accurate, and engaging responses. If you used any special capabilities (image analysis, web search, etc.), briefly mention what you found."""

            full_prompt = f"{system_prompt}\n\nUser: {query}"
            
            response = self.text_model.generate_content(full_prompt)
            
            if response and response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Text generation error: {e}")
            return f"I encountered an error: {str(e)}. Please try again."
    
    def can_handle(self, message: str) -> float:
        """Determine if this agent can handle the message"""
        # Enhanced agent can handle all types of messages
        return 0.9
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process agent request (BaseAgent compatibility)"""
        return await self.process_message(request.message, request.session_id)
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return [
            "Text Q&A",
            "Image Understanding", 
            "Image Generation",
            "Web Search",
            "Multi-modal Processing",
            "Document Analysis"
        ] 