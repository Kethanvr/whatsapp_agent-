from typing import Dict, Any, Optional
import httpx
from .base_agent import BaseAgent, AgentRequest, AgentResponse

class MemoryStoreAgent(BaseAgent):
    """Agent for interacting with a Model Context Protocol memory server.

    It can store and retrieve memories based on user requests.
    Configuration options:
    - memory_url: Base URL of memory server (default: http://localhost:8090)
    - auth_token: Optional bearer token.
    - keywords: keywords to detect memory operations
    """

    def __init__(self, agent_config: Dict[str, Any]):
        super().__init__(agent_config)

        self.memory_url: str = agent_config.get("memory_url", "http://localhost:8090")
        self.auth_token: Optional[str] = agent_config.get("auth_token")
        self.keywords = agent_config.get("keywords", ["remember", "memory", "store", "recall"])
        self._headers = {"Content-Type": "application/json"}
        if self.auth_token:
            self._headers["Authorization"] = f"Bearer {self.auth_token}"

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Handle memory store / retrieve operations."""
        try:
            user_msg = request.message.lower()
            if any(k in user_msg for k in ["remember", "store"]):
                action = "memory.store"
                payload = {
                    "method": action,
                    "params": {
                        "content": request.message,
                        "session_id": request.session_id,
                    },
                }
            else:
                # default to recall
                action = "memory.retrieve"
                payload = {
                    "method": action,
                    "params": {
                        "query": request.message,
                        "session_id": request.session_id,
                    },
                }

            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    f"{self.memory_url}/rpc", json=payload, headers=self._headers
                )
                res.raise_for_status()
                data = res.json()

            result = data.get("result") or "No result"
            return AgentResponse(
                agent_id=self.agent_id,
                response=result,
                confidence=0.85,
                success=True,
                metadata={"action": action, "endpoint": self.memory_url},
            )
        except Exception as e:
            return self._create_error_response(str(e), request)

    def can_handle(self, message: str) -> float:
        msg = message.lower()
        if any(k in msg for k in self.keywords):
            return 0.7
        return 0.2 