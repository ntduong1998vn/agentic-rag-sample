"""
State definitions for RAG Agent.

This module defines the TypedDict classes used to manage state
throughout the LangGraph workflow.
"""

from typing import TypedDict, List, Literal, Optional, Any
from langchain_core.messages import BaseMessage


class QAState(TypedDict, total=False):
    """
    State for the RAG Agent workflow.

    This state is passed through all nodes in the LangGraph and
    accumulates information as the agent processes a question.
    """

    # Input
    question: str  # Original user question

    # Classification
    mode: Literal["simple", "complex"]  # Result of classification

    # Simple path
    messages: List[BaseMessage]  # Tool call/response messages for ToolNode
    simple_answer: Optional[str]

    # Complex path (planning)
    plan: List[str]  # ["Step 1: ...", "Step 2: ..."]
    current_step_index: int
    step_results: List[str]  # Partial answers / notes per step
    working_context: List[Any]  # Docs retrieved across steps
    needs_plan_refine: bool  # Flag when plan needs refinement
    done: bool  # Flag when enough info gathered

    # Output
    final_answer: Optional[str]

    # Iteration control
    iterations: int  # Current refinement iteration count
    max_iterations: int  # Maximum allowed refinement iterations (default: 3)

    # Metadata for context (passed during creation)
    collection_name: str  # Vector store collection name
    chatbot_id: Optional[str]  # Chatbot ID for document lookups
    conversation_id: Optional[str]  # Conversation ID for document lookups
    thread_id: Optional[str]  # Thread ID for chat history tracking
