"""
Base Agent Class

Defines the interface and common functionality for all specialized agents
in the multi-agent orchestration system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class AgentRequest(BaseModel):
    """Request model for agent processing"""
    message: str
    session_id: str
    user_context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    """Response model from agent processing"""
    agent_id: str
    response: str
    confidence: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    Each agent should:
    1. Have a unique ID and capabilities
    2. Process requests and return structured responses
    3. Handle errors gracefully
    4. Provide confidence scores for routing decisions
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        self.agent_id = agent_config.get("id")
        self.name = agent_config.get("name")
        self.description = agent_config.get("description")
        self.capabilities = agent_config.get("capabilities", [])
        self.enabled = agent_config.get("enabled", True)
        self.config = agent_config
        
        logger.info(f"🤖 Initialized {self.name} (ID: {self.agent_id})")
    
    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        Process a user request and return a response.
        
        Args:
            request: AgentRequest containing message and context
            
        Returns:
            AgentResponse with the agent's response and metadata
        """
        pass
    
    @abstractmethod
    def can_handle(self, message: str) -> float:
        """
        Determine if this agent can handle the given message.
        
        Args:
            message: User message to evaluate
            
        Returns:
            Confidence score (0.0 to 1.0) indicating ability to handle
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information for debugging/monitoring"""
        return {
            "id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "enabled": self.enabled
        }
    
    def is_enabled(self) -> bool:
        """Check if agent is enabled"""
        return self.enabled
    
    def _create_error_response(self, error_msg: str, request: AgentRequest) -> AgentResponse:
        """Create a standardized error response"""
        return AgentResponse(
            agent_id=self.agent_id,
            response=f"Sorry, I encountered an error: {error_msg}",
            confidence=0.0,
            success=False,
            error=error_msg
        ) 