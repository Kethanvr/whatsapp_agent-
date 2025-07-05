from typing import Dict, Any, Optional
import httpx
import asyncio
from .base_agent import BaseAgent, AgentRequest, AgentResponse

class GitHubMCPAgent(BaseAgent):
    """Agent that interfaces with a GitHub MCP server instance.

    This wrapper sends RPC-style JSON requests to the GitHub MCP server,
    allowing the WhatsApp AI Assistant to execute GitHub-related tasks
    (e.g. run workflows, fetch README, manage issues) through natural
    language.

    Configuration options (in agents/registry.json):
    - mcp_url: Base URL of the GitHub MCP server (default: http://localhost:8085)
    - auth_token: Optional bearer token for authentication.
    - keywords: List[str] of trigger keywords to increase confidence.
    """

    def __init__(self, agent_config: Dict[str, Any]):
        super().__init__(agent_config)

        self.mcp_url: str = agent_config.get("mcp_url", "http://localhost:8085")
        self.auth_token: Optional[str] = agent_config.get("auth_token")
        # Use config keywords if provided, else repo-related defaults
        self.keywords = agent_config.get(
            "keywords",
            [
                "repo",
                "repository",
                "pull request",
                "pr",
                "issue",
                "github",
                "workflow",
                "commit",
            ],
        )

        # Pre-build headers for HTTP requests
        self._headers = {"Content-Type": "application/json"}
        if self.auth_token:
            self._headers["Authorization"] = f"Bearer {self.auth_token}"

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Translate user request to MCP RPC call and return response."""
        try:
            # For MVP we map every request to `assistant.complete` tool which
            # most MCP servers expose. Users can customise later.
            payload = {
                "method": "assistant.complete",
                "params": {
                    "query": request.message,
                    "session_id": request.session_id,
                },
            }

            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(
                    f"{self.mcp_url}/rpc", headers=self._headers, json=payload
                )
                res.raise_for_status()
                data = res.json()

            result_text = data.get("result") or data.get("response") or "No result"

            return AgentResponse(
                agent_id=self.agent_id,
                response=result_text,
                confidence=0.9,  # High because explicitly chosen
                success=True,
                metadata={"source": "github-mcp", "endpoint": self.mcp_url},
            )

        except Exception as e:
            return self._create_error_response(str(e), request)

    def can_handle(self, message: str) -> float:
        """Return confidence based on presence of GitHub-related keywords."""
        message_lower = message.lower()
        matches = sum(1 for kw in self.keywords if kw in message_lower)
        if matches:
            return min(0.6 + 0.1 * matches, 0.95)
        return 0.1 