"""
Agent Orchestrator - Simple multi-agent routing system

LangGraph-based orchestrator that routes user messages to the most appropriate
specialized agent based on confidence scores and routing rules.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from .base_agent import BaseAgent, AgentRequest, AgentResponse
from .qna_agent import QnAAgent

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Simple Multi-Agent Orchestrator with routing logic"""
    
    def __init__(self, registry_path: str = "agents/registry.json"):
        self.registry_path = Path(registry_path)
        self.agents: Dict[str, BaseAgent] = {}
        self.routing_rules = {}
        
        # Load and initialize
        self._load_registry()
        self._initialize_agents()
        
        logger.info(f"🎯 Orchestrator ready with {len(self.agents)} agents")
    
    def _load_registry(self):
        """Load agent registry"""
        try:
            with open(self.registry_path, 'r') as f:
                registry = json.load(f)
            
            self.agent_configs = registry.get("agents", [])
            self.routing_rules = registry.get("routing_rules", {})
            
        except Exception as e:
            logger.error(f"Failed to load registry: {e}")
            # Use default configuration
            self.agent_configs = [{
                "id": "qna-chatbot",
                "name": "Q&A Assistant", 
                "description": "General question answering",
                "capabilities": ["general-qa", "factual-questions"],
                "model": "gemini-2.5-flash-lite-preview-06-17",
                "temperature": 0.7,
                "max_tokens": 500,
                "enabled": True
            }]
            self.routing_rules = {"default_agent": "qna-chatbot"}
        
    def _initialize_agents(self):
        """Initialize agents"""
        for config in self.agent_configs:
            if config.get("enabled", True):
                try:
                    if config["id"] == "qna-chatbot":
                        agent = QnAAgent(config)
                        self.agents[config["id"]] = agent
                        logger.info(f"✅ Initialized {agent.name}")
                except Exception as e:
                    logger.error(f"Failed to initialize agent {config['id']}: {e}")
    
    async def process_message(self, message: str, session_id: str) -> AgentResponse:
        """Process message through best agent"""
        try:
            if not self.agents:
                return AgentResponse(
                    agent_id="error",
                    response="No agents available",
                    confidence=0.0,
                    success=False,
                    error="No agents initialized"
                )
            
            # Get scores from all agents
            scores = {}
            for agent_id, agent in self.agents.items():
                try:
                    scores[agent_id] = agent.can_handle(message)
                except Exception as e:
                    logger.error(f"Error getting confidence from {agent_id}: {e}")
                    scores[agent_id] = 0.0
            
            # Select best agent
            if scores:
                best_agent_id = max(scores, key=scores.get)
                agent = self.agents[best_agent_id]
            else:
                # Fallback to first available agent
                best_agent_id = list(self.agents.keys())[0]
                agent = self.agents[best_agent_id]
            
            # Process request
            request = AgentRequest(message=message, session_id=session_id)
            response = await agent.process(request)
            
            logger.info(f"✅ Processed by {agent.name} (confidence: {scores.get(best_agent_id, 0.0):.2f})")
            return response
            
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}")
            return AgentResponse(
                agent_id="orchestrator",
                response="Sorry, I'm having technical difficulties.",
                confidence=0.0,
                success=False,
                error=str(e)
            )
    
    def get_agent_info(self) -> List[Dict[str, Any]]:
        """Get information about all loaded agents"""
        return [agent.get_info() for agent in self.agents.values()]
    
    def reload_registry(self):
        """Reload the agent registry and reinitialize agents"""
        logger.info("🔄 Reloading agent registry...")
        self._load_registry()
        self.agents.clear()
        self._initialize_agents()
        logger.info("✅ Registry reloaded successfully") 