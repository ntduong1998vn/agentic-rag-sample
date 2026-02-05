"""
State definitions for the Supervisor (Router) Agent.

Defines the SupervisorState TypedDict used throughout the LangGraph workflow,
along with structured decision models for supervisor LLM outputs.
"""

from enum import Enum
from typing import Annotated, Optional, Literal, TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class SupervisorAction(str, Enum):
    """Actions the supervisor can take."""

    EXECUTE_AGENT = "execute_agent"
    RESPOND = "respond"
    ASK_HUMAN = "ask_human"


class SupervisorDecision(BaseModel):
    """Structured output from the supervisor LLM."""

    action: SupervisorAction = Field(
        description="The next action to take: execute_agent, respond, or ask_human."
    )
    reasoning: str = Field(
        description="Brief reasoning for this decision."
    )
    target_agent: Optional[Literal["gitlab", "rag", "ba", "qc"]] = Field(
        default=None,
        description="Target agent to call. Required when action is execute_agent.",
    )
    agent_input: Optional[str] = Field(
        default=None,
        description="Rewritten input for the target agent. Required when action is execute_agent.",
    )
    response: Optional[str] = Field(
        default=None,
        description="Final response to the user. Required when action is respond.",
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Question to ask the user. Required when action is ask_human.",
    )


class SupervisorState(TypedDict, total=False):
    """
    State for the Supervisor Agent workflow.

    Passed through all nodes in the LangGraph and accumulates
    information as the supervisor orchestrates sub-agents.
    """

    # Input
    question: str
    messages: Annotated[list, add_messages]

    # Preprocessing
    conversation_summary: str
    rewritten_question: str

    # Supervisor loop
    next_action: str  # Routing hint: "execute", "re_decide", "respond"
    target_agent: Optional[str]  # Agent to call next
    agent_input: Optional[str]  # Input for the target agent
    agent_results: dict[str, str]  # Cumulative: {"ba": "...", "qc": "..."}
    selected_agents: list[str]  # History of agents called
    iteration: int  # Loop counter (safety limit)
    max_iterations: int  # Default 5

    # Output
    final_answer: str
    sources: list[dict]

    # Metadata (injected at creation)
    collection_name: str
    chatbot_id: Optional[str]
    conversation_id: Optional[str]
    gitlab_collection_name: Optional[str]
