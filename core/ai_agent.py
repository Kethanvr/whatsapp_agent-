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

# Mapping phone numbers to friendly names
PHONEBOOK = {
    "917483531255": "Kethan (founder)",
    "916360751048": "Keerthi",
    "917022618850": "Kulsum",
    "919945734815": "Divya"
}

BOT_PERSONA_INFO = (
    f"Your name is {settings.bot_name}. You were set up and are maintained by Kethan, "
    "who is your creator and owner. Address Kethan respectfully as 'Kethan'. "
    "You also know these phone-number mappings: "
    "917483531255 → Kethan (founder), 916360751048 → Keerthi, 917022618850 → Kulsum, 919945734815 → Divya. "
    "Use the mapped names instead of raw numbers when you reply."
)

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
                
            # Per-chat history (simple in-memory) for short-term context
            self.chat_histories: Dict[str, list[tuple[str, str]]] = {}
            self.max_history = 5  # remember last 5 exchanges
                
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
        """Process incoming message and generate response with short context"""
        
        lower_q = query.lower().strip()

        # Quick custom Q&A
        custom_answers = {
            "what is your name": f"I'm {settings.bot_name}.",
            "who are you": f"I'm {settings.bot_name}, your AI assistant.",
            "who created you": "I was set up and maintained by Kethan using Google's Gemini model.",
            "who is your founder": "Kethan is my founder and caretaker.",
            "who is kethan": "Kethan is the creator of this bot and the owner of this WhatsApp setup.",
            "who is kethan vr": "Kethan VR is my founder and the one running this system.",
            "who is keerthi": "Keerthi is a friend of Kethan.",
            "who is kulsum": "Kulsum is a friend of Kethan.",
            "who is divya": "Divya is a friend of Kethan."
        }

        for key, val in custom_answers.items():
            if key in lower_q:
                # Update history before returning
                history = self.chat_histories.get(chat_id, [])
                history.append((query, val))
                self.chat_histories[chat_id] = history[-self.max_history:]
                return val

        # If user asks about previous question
        if any(phrase in lower_q for phrase in ["what did i ask", "previous question", "previous answer"]):
            history = self.chat_histories.get(chat_id, [])
            if history:
                last_q, last_a = history[-1]
                summary = f"You previously asked: '{last_q}'."
            else:
                summary = "I don't have any previous question from you in this chat yet."
            # Add to history
            hist = self.chat_histories.get(chat_id, [])
            hist.append((query, summary))
            self.chat_histories[chat_id] = hist[-self.max_history:]
            return summary
        
        # Resolve friendly name if available
        normalized_sender = sender.lstrip("+").split("@")[0]
        friendly_name = PHONEBOOK.get(normalized_sender, sender)
        
        # Build short conversation context
        history = self.chat_histories.get(chat_id, [])
        history_lines = "\n".join([f"{friendly_name}: {q}\n{settings.bot_name}: {r}" for q, r in history[-self.max_history:]])
        if history_lines:
            history_lines = f"Previous conversation (most recent last):\n{history_lines}\n---\n"
        
        system_prompt = f"""
        {BOT_PERSONA_INFO}
        {history_lines}
        Guidelines:
        - Keep responses concise (≤ {settings.max_response_length} chars) and friendly.
        - Address the user by their mapped name if available.
        - If asked what they previously asked, summarize last user message.
        - If you don't know an answer, say so briefly.
        """
        
        messages = [
            SystemMessage(content=system_prompt.strip()),
            HumanMessage(content=query)
        ]
        try:
            logger.info(f"🤖 Generating response for {friendly_name}...")
            # Prefer LangChain call first
            response = self.llm.invoke(messages)
            final_resp = response.content.strip() if response and response.content else ""
            if not final_resp:
                raise ValueError("Empty response")
        except Exception as e:
            logger.warning(f"LangChain failed ({e}); falling back to direct GenAI API")
            try:
                generation_config = genai.types.GenerationConfig(
                    temperature=settings.agent_temperature,
                    max_output_tokens=settings.max_response_length,
                    candidate_count=1,
                    top_p=0.9,
                    top_k=40,
                    response_mime_type="text/plain"
                )
                direct_response = self.direct_model.generate_content(system_prompt.strip() + "\nUser: " + query, generation_config=generation_config)
                final_resp = direct_response.text.strip() if hasattr(direct_response, 'text') else ""
            except Exception as e2:
                logger.error(f"Direct GenAI API failed: {e2}")
                final_resp = "Sorry, I'm having trouble right now."

        if not final_resp:
            final_resp = "Sorry, I'm having trouble right now."

        # Update chat history
        history.append((query, final_resp))
        if len(history) > self.max_history:
            history = history[-self.max_history:]
        self.chat_histories[chat_id] = history

        return final_resp
    
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