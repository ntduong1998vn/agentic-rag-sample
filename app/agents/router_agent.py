"""
Backward-compatible wrapper for the Supervisor (Router) Agent.

All logic has been refactored into the app.agents.router package:
- state.py: SupervisorState, SupervisorDecision, SupervisorAction
- prompts.py: Prompt templates
- tools.py: Sub-agent tool factories
- nodes.py: Node functions (maybe_summarize, rewrite_query, supervisor_decide, etc.)
- graph.py: StateGraph construction, run_router_agent, stream_router_agent

This module re-exports the public API for backward compatibility.
"""

from app.agents.router import (
    create_router_agent,
    run_router_agent,
    stream_router_agent,
)
from app.agents.router.tools import (
    create_gitlab_agent_tool,
    create_rag_agent_tool,
    create_ba_agent_tool,
    create_qc_agent_tool,
    create_load_skill_tool,
)

__all__ = [
    "create_router_agent",
    "run_router_agent",
    "stream_router_agent",
    "create_gitlab_agent_tool",
    "create_rag_agent_tool",
    "create_ba_agent_tool",
    "create_qc_agent_tool",
    "create_load_skill_tool",
]
