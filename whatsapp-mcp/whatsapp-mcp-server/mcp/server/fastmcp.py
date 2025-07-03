"""Minimal lightweight FastMCP implementation.

This stub emulates the subset of the original `fastmcp` library we need
for the WhatsApp MCP server demo so we don't have to pull an external
package.  It dynamically exposes all `@mcp.tool()` decorated callables
as JSON-RPC-style HTTP endpoints and provides a `/health` route for
container liveness checks.
"""
from __future__ import annotations

import inspect
import os
from typing import Callable, Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn


class FastMCP:  # pragma: no cover – simple runtime shim
    """A *very* small subset of the FastMCP API. Enough for this project."""

    def __init__(self, name: str = "mcp") -> None:
        self.app = FastAPI(title=f"{name} FastMCP")

        # Basic health endpoint so Docker health-checks pass
        @self.app.get("/health")
        async def _health() -> Dict[str, str]:  # noqa: WPS430
            return {"status": "ok"}

    # ---------------------------------------------------------------------
    # Decorator to register a function as a tool (HTTP POST endpoint)
    # ---------------------------------------------------------------------
    def tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            endpoint_path = f"/{func.__name__}"

            # FastAPI expects *async* callables – wrap the sync func.
            async def _endpoint(payload: Dict[str, Any]) -> Any:  # noqa: WPS430
                try:
                    # Bind payload to func signature for validation.
                    sig = inspect.signature(func)
                    bound = sig.bind_partial(**payload)
                    bound.apply_defaults()
                    result = func(*bound.args, **bound.kwargs)
                    return result
                except TypeError as exc:  # wrong arguments
                    raise HTTPException(422, str(exc)) from exc
                except Exception as exc:  # pragma: no cover – generic safety
                    raise HTTPException(500, str(exc)) from exc

            # Add route (POST with JSON body)
            self.app.post(endpoint_path)(_endpoint)  # type: ignore[arg-type]
            return func

        return decorator

    # ------------------------------------------------------------------
    # Run server – we treat any transport as HTTP for now.
    # ------------------------------------------------------------------
    def run(self, *, host: str = "0.0.0.0", port: int | None = None, transport: str = "http") -> None:  # noqa: D401
        """Start the FastAPI server.

        The real FastMCP supports multiple transports (stdio/socket).
        For this minimal shim we always launch an HTTP server with
        Uvicorn; if *transport* equals "stdio" we still use HTTP so the
        rest of the code works without changes.
        """
        port = port or int(os.getenv("PORT", "3334"))
        uvicorn.run(self.app, host=host, port=port, log_level="info") 