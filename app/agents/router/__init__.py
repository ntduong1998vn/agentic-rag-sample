"""
Supervisor (Router) Agent package.

Re-exports the public API for creating, running, and streaming the supervisor agent.
"""

from app.agents.router.graph import (
    create_router_agent,
    run_router_agent,
    stream_router_agent,
)

__all__ = [
    "create_router_agent",
    "run_router_agent",
    "stream_router_agent",
]
