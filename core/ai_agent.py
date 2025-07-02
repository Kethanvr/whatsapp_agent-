"""
AI Agent - LangChain + LangGraph + Gemini Integration
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, Any
from loguru import logger
from config.settings import settings
from datetime import datetime
import google.generativeai as genai

class AgentState(TypedDict):
    """State structure for LangGraph agent"""
    query: str
    context: Dict[str, Any]
    response: str
    sender: str
    chat_id: str
    timestamp: str

class WhatsAppAIAgent:
    """Main AI Agent powered by Gemini via LangChain"""
    
    def __init__(self):
        """Initialize the AI agent with Gemini LLM"""
        try:
            # Configure Google GenAI directly for 2.0+ models (more reliable)
            genai.configure(api_key=settings.gemini_api_key)
            
            # Always use direct GenAI for gemini-2.0-flash (no thinking mode)
            logger.info(f"🔧 Using direct GenAI for {settings.agent_model} with thinking disabled")
            
            # Use direct GenAI for reliable 2.0 flash responses
            self.direct_model = genai.GenerativeModel(
                model_name=settings.agent_model,
                system_instruction="You are a helpful AI assistant. Provide clear, concise responses without showing your thinking process or reasoning steps.",
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                ]
            )
            
            # Initialize LangChain without thinking parameters
            self.llm = ChatGoogleGenerativeAI(
                model=settings.agent_model,
                google_api_key=settings.gemini_api_key,
                temperature=settings.agent_temperature,
                max_output_tokens=settings.max_response_length,
                top_p=0.9,
                top_k=40,
                # Explicitly disable thinking mode parameters
                thinking_budget=None,
                include_thoughts=False
            )
            self.use_direct_api = True
                
            logger.info(f"🧠 AI Agent initialized with model: {settings.agent_model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Agent: {e}")
            raise e
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for message processing"""
        
        def analyze_intent(state: AgentState) -> AgentState:
            """Analyze the intent of the user query"""
            query = state["query"]
            
            # For MVP, we'll do simple intent classification
            intent_prompt = f"""
            Analyze this WhatsApp message and classify the intent:
            Message: "{query}"
            
            Is this:
            1. A question that needs an informative answer
            2. A casual conversation/greeting
            3. A request for help/assistance
            4. Other
            
            Respond with just the category number and a brief reason.
            """
            
            try:
                intent_response = self.llm.invoke([HumanMessage(content=intent_prompt)])
                state["context"]["intent"] = intent_response.content
            except Exception as e:
                logger.error(f"Intent analysis failed: {e}")
                state["context"]["intent"] = "question"
            
            return state
        
        def generate_response(state: AgentState) -> AgentState:
            """Generate AI response using Gemini"""
            query = state["query"]
            sender = state["sender"]
            
            system_prompt = f"""
            You are {settings.bot_name}, a helpful AI assistant integrated with WhatsApp.
            
            Guidelines:
            - Keep responses concise and conversational (max {settings.max_response_length} chars)
            - Be helpful, friendly, and informative
            - If you don't know something, say so honestly
            - For greetings, respond naturally
            - For questions, provide clear, accurate answers
            - Use emojis sparingly but appropriately
            
            The user's name/number is: {sender}
            Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            
            try:
                logger.info(f"🤖 Generating response for {sender}...")
                response = self.llm.invoke(messages)
                
                if response and response.content:
                    state["response"] = response.content.strip()
                    logger.info(f"✅ Response generated: {response.content[:50]}...")
                else:
                    logger.warning("⚠️ Empty response from LLM")
                    state["response"] = "I apologize, but I wasn't able to generate a proper response. Please try rephrasing your question."
                
            except Exception as e:
                logger.error(f"❌ Response generation failed: {str(e)}")
                
                # Provide helpful fallback based on error type
                if "safety" in str(e).lower():
                    state["response"] = "I can't provide a response to that due to safety guidelines. Please try rephrasing your question."
                elif "quota" in str(e).lower() or "limit" in str(e).lower():
                    state["response"] = "I'm experiencing high demand right now. Please try again in a moment."
                else:
                    state["response"] = "Sorry, I'm experiencing technical difficulties. Please try again later."
            
            return state
        
        def format_output(state: AgentState) -> AgentState:
            """Format the final response"""
            response = state["response"]
            
            # Ensure response isn't too long
            if len(response) > settings.max_response_length:
                response = response[:settings.max_response_length - 3] + "..."
                state["response"] = response
            
            return state
        
        # Build the workflow graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_intent", analyze_intent)
        workflow.add_node("generate_response", generate_response)
        workflow.add_node("format_output", format_output)
        
        # Add edges
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "generate_response")
        workflow.add_edge("generate_response", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow
    
    def process_message(self, query: str, sender: str, chat_id: str) -> str:
        """Process incoming message and generate response"""
        
        initial_state = AgentState(
            query=query,
            context={"intent": None},
            response="",
            sender=sender,
            chat_id=chat_id,
            timestamp=datetime.now().isoformat()
        )
        
        try:
            # Run the LangGraph workflow
            result = self.app.invoke(initial_state)
            return result["response"]
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return "I apologize, but I encountered an error while processing your message. Please try again."
    
    def get_simple_response(self, query: str, sender: str = "User") -> str:
        """Simple response generation for testing/debugging"""
        try:
            logger.info(f"🔄 Generating simple response for: {query[:30]}...")
            
            # Use direct API for 2.0+ models to avoid thinking mode issues
            if self.use_direct_api and self.direct_model:
                logger.info("📡 Using direct GenAI API (thinking disabled)")
                
                generation_config = genai.types.GenerationConfig(
                    temperature=settings.agent_temperature,
                    max_output_tokens=settings.max_response_length,
                    candidate_count=1,
                    top_p=0.9,
                    top_k=40,
                    response_mime_type="text/plain"
                )
                
                response = self.direct_model.generate_content(
                    query,
                    generation_config=generation_config
                )
                
                if response and hasattr(response, 'text') and response.text:
                    result = response.text.strip()
                    logger.info(f"✅ Direct API response: {result[:50]}...")
                    return result
                else:
                    logger.warning("⚠️ Empty response from direct API")
                    return "I apologize, but I wasn't able to generate a response. Please try again."
            
            else:
                # Use LangChain for older models
                logger.info("🔗 Using LangChain API")
                
                messages = [
                    SystemMessage(content=f"You are {settings.bot_name}, a helpful AI assistant. Keep responses concise and friendly."),
                    HumanMessage(content=query)
                ]
                
                response = self.llm.invoke(messages)
                
                if response and response.content:
                    result = response.content.strip()
                    logger.info(f"✅ LangChain response: {result[:50]}...")
                    return result
                else:
                    logger.warning("⚠️ Empty LangChain response")
                    return "I apologize, but I wasn't able to generate a response. Please try again."
            
        except Exception as e:
            logger.error(f"❌ Simple response generation failed: {str(e)}")
            
            # Return helpful fallback based on error type
            if "thinking" in str(e).lower() or "unknown field" in str(e).lower():
                return "I'm experiencing technical issues with the AI model. Please try again."
            elif "what" in query.lower() or "?" in query:
                return "I'm sorry, I'm having technical issues and can't answer your question right now. Please try again."
            else:
                return "I apologize for the technical difficulties. Please try your request again."

# Global agent instance
ai_agent = WhatsAppAIAgent()