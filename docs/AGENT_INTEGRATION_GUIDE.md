# ��� Agent Integration Guide

## Overview

This guide explains how to add new AI agents to the WhatsApp AI Assistant system. Most agents will be **locally running services** cloned from GitHub repositories and modified to work with our orchestration system.

## Self-Invocation Support

**Yes, you CAN invoke the AI assistant yourself!** The system supports:

### Self-Testing

- Send `!ask` messages to yourself in WhatsApp
- Test different agents and capabilities
- Debug responses and routing

### Configuration for Self-Use

```env
# Allow your own number (optional)
AUTHORIZED_NUMBERS=+1234567890

# Or leave empty to allow all numbers including yourself
AUTHORIZED_NUMBERS=
```

### Dashboard Testing

- Use the Streamlit dashboard at `http://localhost:8503`
- Test agents without WhatsApp
- Send messages to any contact including yourself

## Integration Patterns

### Pattern 1: Direct Agent Integration

For agents that can be modified to inherit from our base class.

### Pattern 2: API Wrapper Integration

For existing services that expose APIs.

### Pattern 3: MCP Server Integration

For Model Context Protocol compatible services.

## Adding a New Direct Agent

### Step 1: Create Agent Class

Create `agents/your_agent.py`:

```python
import asyncio
from typing import Dict, Any
from .base_agent import BaseAgent, AgentRequest, AgentResponse

class YourAgent(BaseAgent):
    """Specialized agent for [describe purpose]"""

    def __init__(self, agent_config: Dict[str, Any]):
        super().__init__(agent_config)

        # Agent-specific keywords for routing
        self.keywords = ["keyword1", "keyword2", "keyword3"]

        print(f"��� {self.name} initialized")

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process request using your agent logic"""
        try:
            user_message = request.message.strip()

            # Your agent processing logic here
            response_text = await self._generate_response(user_message)

            return AgentResponse(
                agent_id=self.agent_id,
                response=response_text,
                confidence=0.8,
                success=True,
                metadata={"model": "your-model"}
            )

        except Exception as e:
            return self._create_error_response(str(e), request)

    def can_handle(self, message: str) -> float:
        """Calculate confidence for handling this message"""
        message_lower = message.lower()
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message_lower)

        confidence = 0.3  # Base confidence
        if keyword_matches > 0:
            confidence += min(keyword_matches * 0.2, 0.5)

        return min(confidence, 0.9)

    async def _generate_response(self, message: str) -> str:
        """Your custom response generation logic"""
        return f"Response from {self.name}: {message}"
```

### Step 2: Register Agent

Add to `agents/registry.json`:

```json
{
  "agents": [
    {
      "id": "your-agent",
      "name": "Your Agent Name",
      "description": "Description of what your agent does",
      "capabilities": ["capability-1", "capability-2"],
      "model": "your-model-name",
      "enabled": true
    }
  ],
  "routing_rules": {
    "keywords": {
      "your-agent": ["keyword1", "keyword2", "keyword3"]
    }
  }
}
```

### Step 3: Update Orchestrator

Modify `agents/orchestrator.py` to import your agent:

```python
# Add import
from .your_agent import YourAgent

class AgentOrchestrator:
    def _initialize_agents(self):
        for agent_config in self.registry["agents"]:
            agent_id = agent_config["id"]

            # Add your agent
            if agent_id == "your-agent":
                agent = YourAgent(agent_config)
                self.agents[agent_id] = agent
```

## Local Agent Development Pattern

### Recommended Structure

```
whatsapp-agent/
├── external-agents/                 # Local agent repositories
│   ├── code-agent/                 # Cloned from GitHub
│   │   ├── server.py              # Modified to work with us
│   │   └── requirements.txt
│   ├── search-agent/              # Cloned from GitHub
│   │   └── main.py               # Modified integration
│   └── custom-mcp/               # Your custom MCP server
│       └── server.py
├── agents/                       # Agent wrappers
│   ├── code_agent_wrapper.py    # Wrapper for external code agent
│   └── search_agent_wrapper.py  # Wrapper for external search agent
```

### Startup Script for Multiple Agents

Create `start_all_agents.sh`:

```bash
#!/bin/bash

echo "��� Starting all AI agents..."

# Start external agents
cd external-agents/code-agent && python server.py --port 8081 &
cd external-agents/search-agent && python main.py --port 8082 &

# Wait for agents to start
sleep 5

# Start main WhatsApp AI system
cd ../..
python main.py

echo "✅ All agents started!"
```

## Testing New Agents

### Test Individual Agent

```python
# test_your_agent.py
import asyncio
from agents.your_agent import YourAgent
from agents.base_agent import AgentRequest

async def test_agent():
    config = {"id": "test-agent", "name": "Test Agent"}
    agent = YourAgent(config)
    request = AgentRequest(message="test message", session_id="test")

    response = await agent.process(request)
    print(f"Success: {response.success}")
    print(f"Response: {response.response}")

if __name__ == "__main__":
    asyncio.run(test_agent())
```

## Quick Start Checklist

- [ ] Create agent class inheriting from `BaseAgent`
- [ ] Implement `process()` and `can_handle()` methods
- [ ] Add agent configuration to `agents/registry.json`
- [ ] Update orchestrator imports
- [ ] Test individual agent functionality
- [ ] Test routing and confidence scoring
- [ ] Test end-to-end WhatsApp integration

This guide provides a flexible foundation for integrating any type of AI agent or service into your WhatsApp AI Assistant system!
