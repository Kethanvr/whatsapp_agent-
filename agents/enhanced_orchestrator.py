"""
Enhanced Multi-Agent Orchestrator with A2A Protocol
- Agent-to-Agent (A2A) Communication
- LangGraph-style workflow orchestration  
- Multi-modal message processing
- Dynamic agent collaboration
- Capability-based routing
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from loguru import logger
from datetime import datetime

from .base_agent import BaseAgent, AgentRequest, AgentResponse
from .qna_agent import QnAAgent
from .enhanced_qna_agent import EnhancedQnAAgent, MediaContent
from .sub_agents.image_specialist_agent import ImageSpecialistAgent
from .sub_agents.web_search_agent import WebSearchAgent

@dataclass
class WorkflowNode:
    """Represents a node in the agent workflow graph"""
    agent_id: str
    task_type: str
    dependencies: List[str] = None
    output_keys: List[str] = None
    condition: Optional[str] = None

@dataclass 
class AgentMessage:
    """Message passed between agents in A2A protocol"""
    sender_id: str
    receiver_id: str
    message_type: str  # 'request', 'response', 'data', 'error'
    content: Any
    metadata: Dict = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}

class EnhancedAgentOrchestrator:
    """Enhanced Multi-Agent Orchestrator with A2A Protocol"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, List[WorkflowNode]] = {}
        self.message_bus: Dict[str, List[AgentMessage]] = {}
        
        self._initialize_agents()
        self._setup_workflows()
        self._setup_capabilities()
        
        logger.info(f"🚀 Enhanced Orchestrator initialized with {len(self.agents)} agents")
    
    def _initialize_agents(self):
        """Initialize all specialized agents"""
        try:
            # Core agents
            self.agents["enhanced_qna"] = EnhancedQnAAgent()
            
            # Fallback QnA agent with proper config
            fallback_config = {
                "id": "qna-chatbot",
                "name": "Q&A Assistant", 
                "description": "General question answering",
                "capabilities": ["general-qa", "factual-questions"],
                "model": "gemini-2.0-flash",
                "temperature": 0.7,
                "max_tokens": 300,
                "enabled": True
            }
            self.agents["qna_fallback"] = QnAAgent(fallback_config)
            
            # Specialist sub-agents
            self.agents["image_specialist"] = ImageSpecialistAgent()
            self.agents["web_search"] = WebSearchAgent()
            
            logger.info("✅ All agents initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            # Fallback to basic QnA only
            fallback_config = {
                "id": "qna-chatbot",
                "name": "Q&A Assistant", 
                "description": "General question answering fallback",
                "capabilities": ["general-qa"],
                "enabled": True
            }
            self.agents["qna_fallback"] = QnAAgent(fallback_config)
    
    def _setup_workflows(self):
        """Setup predefined workflows for different request types"""
        
        # Standard Q&A workflow
        self.workflows["standard_qa"] = [
            WorkflowNode("enhanced_qna", "primary_processing")
        ]
        
        # Image analysis workflow
        self.workflows["image_analysis"] = [
            WorkflowNode("image_specialist", "image_processing", output_keys=["image_analysis"]),
            WorkflowNode("enhanced_qna", "integration", dependencies=["image_specialist"])
        ]
        
        # Web search workflow
        self.workflows["web_search"] = [
            WorkflowNode("web_search", "search_processing", output_keys=["search_results"]),
            WorkflowNode("enhanced_qna", "synthesis", dependencies=["web_search"])
        ]
        
        # Multi-modal workflow (images + search)
        self.workflows["multimodal"] = [
            WorkflowNode("image_specialist", "image_processing", output_keys=["image_analysis"]),
            WorkflowNode("web_search", "search_processing", output_keys=["search_results"]),
            WorkflowNode("enhanced_qna", "final_synthesis", dependencies=["image_specialist", "web_search"])
        ]
        
        # Image generation workflow
        self.workflows["image_generation"] = [
            WorkflowNode("web_search", "reference_search", output_keys=["references"], 
                        condition="needs_reference"),
            WorkflowNode("image_specialist", "image_generation", dependencies=["web_search"])
        ]
        
        logger.info(f"🔄 Workflows configured: {list(self.workflows.keys())}")
    
    def _setup_capabilities(self):
        """Map capabilities to agents"""
        self.capability_map = {
            "text_qa": ["enhanced_qna", "qna_fallback"],
            "image_understanding": ["image_specialist"],
            "image_generation": ["image_specialist"],
            "web_search": ["web_search"],
            "current_events": ["web_search"],
            "multimodal": ["enhanced_qna"],
            "ocr": ["image_specialist"],
            "news": ["web_search"]
        }
    
    async def process_message(self, message: str, session_id: str, 
                            media: Optional[List[MediaContent]] = None) -> AgentResponse:
        """Process message through orchestrated agent workflow"""
        try:
            logger.info(f"🎯 Processing: '{message[:50]}...' with {len(media) if media else 0} media items")
            
            # Analyze request to determine optimal workflow
            workflow_type = self._determine_workflow(message, media)
            logger.info(f"📋 Selected workflow: {workflow_type}")
            
            # Execute workflow
            if workflow_type in self.workflows:
                result = await self._execute_workflow(workflow_type, message, session_id, media)
            else:
                # Fallback to single agent
                result = await self._fallback_processing(message, session_id, media)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}")
            return AgentResponse(
                success=False,
                response="I encountered an error processing your request. Please try again.",
                agent_id="orchestrator", 
                error=str(e)
            )
    
    def _determine_workflow(self, message: str, media: Optional[List[MediaContent]]) -> str:
        """Determine optimal workflow based on message content and media"""
        message_lower = message.lower()
        has_images = media and any(m.type == 'image' for m in media)
        
        # Multi-modal workflow (images + potential search)
        if has_images and any(word in message_lower for word in 
                             ['search', 'find', 'latest', 'current', 'news', 'what is']):
            return "multimodal"
        
        # Image generation
        if any(word in message_lower for word in 
               ['generate', 'create', 'make', 'draw', 'design']) and \
           any(word in message_lower for word in ['image', 'picture', 'art', 'photo']):
            return "image_generation"
        
        # Image analysis only
        if has_images:
            return "image_analysis"
        
        # Web search for current information
        if any(word in message_lower for word in 
               ['current', 'latest', 'news', 'today', 'recent', 'search', 'weather']):
            return "web_search"
        
        # Standard Q&A
        return "standard_qa"
    
    async def _execute_workflow(self, workflow_type: str, message: str, session_id: str, 
                               media: Optional[List[MediaContent]]) -> AgentResponse:
        """Execute a specific workflow with agent coordination"""
        workflow = self.workflows[workflow_type]
        context = {"original_message": message, "session_id": session_id, "media": media}
        results = {}
        
        logger.info(f"🔄 Executing {workflow_type} workflow with {len(workflow)} steps")
        
        for step, node in enumerate(workflow):
            try:
                logger.info(f"📍 Step {step + 1}: {node.agent_id} - {node.task_type}")
                
                # Check dependencies
                if node.dependencies:
                    missing_deps = [dep for dep in node.dependencies if dep not in results]
                    if missing_deps:
                        logger.warning(f"⚠️ Missing dependencies: {missing_deps}")
                        continue
                
                # Check condition
                if node.condition and not self._evaluate_condition(node.condition, context, results):
                    logger.info(f"⏭️ Skipping step due to condition: {node.condition}")
                    continue
                
                # Execute agent task
                agent = self.agents.get(node.agent_id)
                if not agent:
                    logger.error(f"❌ Agent not found: {node.agent_id}")
                    continue
                
                # Prepare agent input based on task type and dependencies
                agent_input = self._prepare_agent_input(node, context, results)
                
                # Execute agent
                if node.agent_id == "enhanced_qna":
                    response = await agent.process_message(
                        agent_input["query"], 
                        session_id, 
                        media=agent_input.get("media")
                    )
                elif node.agent_id == "image_specialist":
                    response = await agent.process_message(
                        agent_input["query"], 
                        session_id,
                        **agent_input.get("kwargs", {})
                    )
                elif node.agent_id == "web_search":
                    response = await agent.process_message(
                        agent_input["query"], 
                        session_id,
                        **agent_input.get("kwargs", {})
                    )
                else:
                    # Fallback for standard agents
                    request = AgentRequest(message=agent_input["query"], session_id=session_id)
                    response = await agent.process(request)
                
                # Store results
                results[node.agent_id] = response
                
                # Store outputs with specific keys
                if node.output_keys:
                    for key in node.output_keys:
                        results[key] = response.response
                
                logger.info(f"✅ Step {step + 1} completed: {response.success}")
                
                # Send A2A message if needed
                await self._send_a2a_message(
                    sender_id=node.agent_id,
                    receiver_id="orchestrator", 
                    message_type="response",
                    content=response
                )
                
            except Exception as e:
                logger.error(f"❌ Workflow step {step + 1} failed: {e}")
                continue
        
        # Return the final result (usually from the last agent)
        if results:
            final_result = list(results.values())[-1]
            if isinstance(final_result, AgentResponse):
                final_result.metadata = final_result.metadata or {}
                final_result.metadata["workflow"] = workflow_type
                final_result.metadata["steps_completed"] = len(results)
                return final_result
        
        # Fallback if workflow failed
        return await self._fallback_processing(message, session_id, media)
    
    def _prepare_agent_input(self, node: WorkflowNode, context: Dict, results: Dict) -> Dict:
        """Prepare input for agent based on node configuration and previous results"""
        base_input = {
            "query": context["original_message"],
            "kwargs": {}
        }
        
        # Add media for image processing
        if node.agent_id == "image_specialist" and context.get("media"):
            base_input["kwargs"]["image_data"] = context["media"][0].data if context["media"] else None
            base_input["kwargs"]["image_url"] = context["media"][0].url if context["media"] else None
        
        # Add enhanced query for synthesis tasks
        if node.task_type in ["integration", "synthesis", "final_synthesis"]:
            enhanced_parts = [context["original_message"]]
            
            # Add previous results as context
            for dep in node.dependencies or []:
                if dep in results and hasattr(results[dep], 'response'):
                    enhanced_parts.append(f"Previous analysis from {dep}: {results[dep].response}")
            
            base_input["query"] = "\n\n".join(enhanced_parts)
        
        # Add media to enhanced_qna
        if node.agent_id == "enhanced_qna":
            base_input["media"] = context.get("media")
        
        return base_input
    
    def _evaluate_condition(self, condition: str, context: Dict, results: Dict) -> bool:
        """Evaluate workflow condition"""
        if condition == "needs_reference":
            # Check if image generation needs web reference
            message = context["original_message"].lower()
            return any(word in message for word in ['current', 'latest', 'trending', 'popular'])
        
        return True
    
    async def _fallback_processing(self, message: str, session_id: str, 
                                  media: Optional[List[MediaContent]]) -> AgentResponse:
        """Fallback to single agent processing"""
        logger.info("🔄 Using fallback processing")
        
        # Try enhanced QnA first
        if "enhanced_qna" in self.agents:
            try:
                return await self.agents["enhanced_qna"].process_message(message, session_id, media)
            except Exception as e:
                logger.warning(f"Enhanced QnA failed: {e}")
        
        # Fallback to basic QnA
        if "qna_fallback" in self.agents:
            request = AgentRequest(message=message, session_id=session_id)
            return await self.agents["qna_fallback"].process(request)
        
        # Ultimate fallback
        return AgentResponse(
            success=False,
            response="No agents available to process your request.",
            agent_id="fallback",
            error="All agents failed"
        )
    
    async def _send_a2a_message(self, sender_id: str, receiver_id: str, 
                               message_type: str, content: Any):
        """Send agent-to-agent message through message bus"""
        message = AgentMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content
        )
        
        if receiver_id not in self.message_bus:
            self.message_bus[receiver_id] = []
        
        self.message_bus[receiver_id].append(message)
        logger.debug(f"📨 A2A Message: {sender_id} → {receiver_id} ({message_type})")
    
    def get_agent_info(self) -> List[Dict[str, Any]]:
        """Get information about all agents and their capabilities"""
        info = []
        for agent_id, agent in self.agents.items():
            agent_info = {
                "id": agent_id,
                "name": getattr(agent, 'name', agent_id),
                "description": getattr(agent, 'description', 'No description'),
                "capabilities": getattr(agent, 'get_capabilities', lambda: [])(),
                "status": "active"
            }
            info.append(agent_info)
        
        return info
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """Get information about available workflows"""
        return {
            "workflows": list(self.workflows.keys()),
            "workflow_details": {
                name: [asdict(node) for node in workflow] 
                for name, workflow in self.workflows.items()
            },
            "capabilities": self.capability_map
        }
    
    def get_a2a_messages(self, agent_id: str, limit: int = 10) -> List[AgentMessage]:
        """Get recent A2A messages for an agent"""
        messages = self.message_bus.get(agent_id, [])
        return messages[-limit:] if messages else [] 