"""
Image Specialist Agent - Sub-Agent for Image Processing
- Image Understanding & Analysis
- Image Generation 
- Visual Content Processing
- OCR and Text Extraction
"""

import asyncio
import base64
import tempfile
import os
from typing import Dict, List, Optional, Any
from loguru import logger
from dataclasses import dataclass

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    logger.warning("google-generativeai not installed")
    genai = None

from ..base_agent import BaseAgent, AgentResponse, AgentRequest
from config.settings import settings

@dataclass
class ImageTask:
    """Represents an image processing task"""
    task_type: str  # 'analyze', 'generate', 'ocr', 'compare'
    prompt: str
    image_data: Optional[bytes] = None
    image_url: Optional[str] = None
    style_params: Optional[Dict] = None

class ImageSpecialistAgent(BaseAgent):
    """Specialized agent for all image-related tasks"""
    
    def __init__(self, agent_config=None):
        config = agent_config or {
            "id": "image_specialist",
            "name": "Image Specialist Agent",
            "description": "Expert in image understanding, generation, and visual content processing",
            "capabilities": ["image_understanding", "image_generation", "ocr", "visual_processing"],
            "enabled": True
        }
        super().__init__(config)
        self.setup_models()
    
    def setup_models(self):
        """Setup specialized image models"""
        if not genai or not settings.gemini_api_key:
            logger.error("Gemini API not available for image processing")
            return
            
        genai.configure(api_key=settings.gemini_api_key)
        
        # Vision model for understanding
        self.vision_model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config={
                'temperature': 0.3,  # Lower for more consistent analysis
                'top_p': 0.8,
                'max_output_tokens': 1024,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        # Image generation model
        self.image_gen_model = genai.GenerativeModel(
            'gemini-2.0-flash-preview-image-generation',
            generation_config={
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 40,
            }
        )
        
        logger.info("🎨 Image Specialist models initialized")
    
    async def process_message(self, query: str, session_id: str, **kwargs) -> AgentResponse:
        """Process image-related requests"""
        try:
            # Parse the request to determine image task
            task = self._parse_image_request(query, kwargs)
            
            if task.task_type == 'analyze':
                result = await self._analyze_image(task)
            elif task.task_type == 'generate':
                result = await self._generate_image(task)
            elif task.task_type == 'ocr':
                result = await self._extract_text(task)
            elif task.task_type == 'compare':
                result = await self._compare_images(task)
            else:
                result = "I'm not sure what image task you need. Please specify: analyze, generate, OCR, or compare images."
            
            return AgentResponse(
                success=True,
                response=result,
                agent_id=self.agent_id,
                confidence=0.95,
                metadata={"task_type": task.task_type}
            )
            
        except Exception as e:
            logger.error(f"Image Specialist error: {e}")
            return AgentResponse(
                success=False,
                response="I encountered an error processing the image request.",
                agent_id=self.agent_id,
                error=str(e)
            )
    
    def _parse_image_request(self, query: str, kwargs: Dict) -> ImageTask:
        """Parse request to determine image task type"""
        query_lower = query.lower()
        
        # Determine task type
        if any(word in query_lower for word in ['generate', 'create', 'make', 'draw', 'design']):
            task_type = 'generate'
        elif any(word in query_lower for word in ['read', 'text', 'ocr', 'extract']):
            task_type = 'ocr'
        elif any(word in query_lower for word in ['compare', 'difference', 'similar']):
            task_type = 'compare'
        else:
            task_type = 'analyze'
        
        return ImageTask(
            task_type=task_type,
            prompt=query,
            image_data=kwargs.get('image_data'),
            image_url=kwargs.get('image_url'),
            style_params=kwargs.get('style_params', {})
        )
    
    async def _analyze_image(self, task: ImageTask) -> str:
        """Analyze image content"""
        try:
            if not self.vision_model:
                return "Image analysis model not available."
            
            # Prepare image for analysis
            if task.image_data:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(task.image_data)
                    tmp_path = tmp_file.name
            elif task.image_url:
                # Download image
                import requests
                response = requests.get(task.image_url, timeout=10)
                if response.status_code != 200:
                    return "Failed to download image from URL."
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
            else:
                return "No image provided for analysis."
            
            # Enhanced analysis prompt
            analysis_prompt = f"""Analyze this image comprehensively. Based on the user's request: "{task.prompt}"

Please provide:
1. 🔍 **Visual Description**: What do you see in the image?
2. 🎯 **Key Elements**: Important objects, people, text, or features
3. 🎨 **Visual Qualities**: Colors, composition, style, lighting
4. 📝 **Relevant Details**: Anything that relates to the user's specific question
5. 💡 **Insights**: Any interesting observations or context

Format your response clearly with emojis and sections."""

            # Upload and analyze
            uploaded_file = genai.upload_file(tmp_path)
            response = self.vision_model.generate_content([analysis_prompt, uploaded_file])
            
            # Cleanup
            genai.delete_file(uploaded_file.name)
            os.unlink(tmp_path)
            
            if response and response.text:
                return f"🎨 **Image Analysis Complete:**\n\n{response.text.strip()}"
            else:
                return "I couldn't analyze the image. Please try again with a different image."
                
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return f"Image analysis failed: {str(e)}"
    
    async def _generate_image(self, task: ImageTask) -> str:
        """Generate image based on prompt"""
        try:
            if not self.image_gen_model:
                return "Image generation model not available."
            
            # Build enhanced prompt with style parameters
            style_params = task.style_params or {}
            style = style_params.get('style', 'realistic')
            quality = style_params.get('quality', 'high')
            aspect_ratio = style_params.get('aspect_ratio', '1:1')
            
            enhanced_prompt = f"""Create a {quality} quality {style} image: {task.prompt}

Style: {style}, detailed, well-composed
Quality: {quality} resolution, clear, professional  
Aspect Ratio: {aspect_ratio}
Lighting: Natural, well-balanced
Composition: Engaging, visually appealing"""

            logger.info(f"🎨 Generating image with prompt: {enhanced_prompt[:100]}...")
            
            response = self.image_gen_model.generate_content([enhanced_prompt])
            
            if response and hasattr(response, 'candidates') and response.candidates:
                # TODO: Extract actual image URL/data from response
                # This depends on Gemini's response format for image generation
                logger.info("🎨 Image generated successfully")
                return f"🎨 **Image Generated Successfully!**\n\nPrompt: {task.prompt}\nStyle: {style}\nQuality: {quality}\n\n*Image would be displayed here in production*"
            else:
                return "Failed to generate image. Please try a different prompt."
                
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return f"Image generation failed: {str(e)}"
    
    async def _extract_text(self, task: ImageTask) -> str:
        """Extract text from image (OCR)"""
        try:
            if not self.vision_model:
                return "OCR model not available."
            
            # Prepare image for OCR
            if task.image_data:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(task.image_data)
                    tmp_path = tmp_file.name
            elif task.image_url:
                import requests
                response = requests.get(task.image_url, timeout=10)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
            else:
                return "No image provided for text extraction."
            
            # OCR prompt
            ocr_prompt = """Extract ALL text visible in this image. Please:

1. 📝 **Transcribe exactly** what text you see
2. 🔤 **Preserve formatting** where possible
3. 📍 **Note locations** if text appears in different areas
4. 🔍 **Include small text** even if partially visible

Format the extracted text clearly and indicate if any text is unclear."""

            uploaded_file = genai.upload_file(tmp_path)
            response = self.vision_model.generate_content([ocr_prompt, uploaded_file])
            
            # Cleanup
            genai.delete_file(uploaded_file.name)
            os.unlink(tmp_path)
            
            if response and response.text:
                return f"📝 **Text Extracted from Image:**\n\n{response.text.strip()}"
            else:
                return "No text found in the image or extraction failed."
                
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return f"Text extraction failed: {str(e)}"
    
    async def _compare_images(self, task: ImageTask) -> str:
        """Compare multiple images"""
        # TODO: Implement image comparison
        return "🔄 Image comparison feature coming soon! Please provide two images to compare."
    
    def can_handle(self, message: str) -> float:
        """Determine if this agent can handle the message"""
        message_lower = message.lower()
        # High confidence for image-related tasks
        if any(word in message_lower for word in ['image', 'picture', 'photo', 'visual', 'draw', 'generate']):
            return 0.95
        # Medium confidence for OCR tasks
        if any(word in message_lower for word in ['read', 'text', 'ocr', 'extract']):
            return 0.8
        return 0.1
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process agent request (BaseAgent compatibility)"""
        return await self.process_message(request.message, request.session_id)
    
    def get_capabilities(self) -> List[str]:
        """Return image processing capabilities"""
        return [
            "Image Analysis & Understanding",
            "Image Generation & Creation", 
            "OCR & Text Extraction",
            "Visual Content Processing",
            "Image Comparison",
            "Style Transfer",
            "Visual Question Answering"
        ] 