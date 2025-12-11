"""
State definitions for GitLab Agent.

This module defines the TypedDict classes used to manage state
throughout the LangGraph workflow.
"""

from typing import TypedDict, List, Literal, Optional


class PlanStep(TypedDict):
    """A single step in the execution plan."""

    step_id: int
    action: Literal["retrieve", "reason", "diagram"]
    description: str  # What this step does
    query: str  # Query for retrieval or reasoning context
    status: Literal["pending", "in_progress", "completed", "skipped"]
    result: Optional[str]  # Result after execution


class AgentState(TypedDict):
    """
    State for the GitLab Agent workflow.

    This state is passed through all nodes in the LangGraph and
    accumulates information as the agent processes a question.
    """

    # Input
    question: str  # Original user question

    # Classification
    question_type: Literal["simple", "complex"]  # Result of classification

    # Planning (for complex questions)
    plan: List[PlanStep]  # List of planned steps
    current_step_index: int  # Index of current step being executed

    # Execution results
    retrieved_docs: List[str]  # Documents retrieved from vector store
    intermediate_results: List[str]  # Results from reasoning steps
    diagrams: List[str]  # Generated Mermaid/PlantUML diagrams

    # Output
    final_answer: str  # Final synthesized answer

    # Control flow
    iterations: int  # Current refinement iteration count
    max_iterations: int  # Maximum allowed refinement iterations (default: 3)
    current_action: Optional[str]  # Current action being executed
