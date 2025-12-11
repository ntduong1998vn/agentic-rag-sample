"""
GitLab Agent using LangGraph StateGraph.

This agent can handle simple and complex questions about a codebase/documentation,
with multi-step planning, execution, and refinement capabilities.
"""

from typing import List, Optional
from functools import partial

from langgraph.graph import StateGraph, END

from app.core.logging import get_logger
from app.agents.workflows.gitlab_agent.state import AgentState
from app.agents.workflows.gitlab_agent.nodes import (
    classify_question,
    simple_rag,
    planner,
    execute_step,
    refine_plan,
    synthesize_answer,
)

logger = get_logger(__name__)


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================


def route_by_complexity(state: AgentState) -> str:
    """Route based on question complexity."""
    return state["question_type"]


def route_after_execute(state: AgentState) -> str:
    """Route after step execution."""
    current_index = state["current_step_index"]
    plan = state["plan"]

    if current_index >= len(plan):
        return "refine"
    return "execute"


def route_after_refine(state: AgentState) -> str:
    """Route after plan refinement."""
    action = state.get("current_action", "continue")

    if action == "complete":
        return "synthesize"
    return "execute"


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================


def create_gitlab_agent(
    collection_name: str,
    checkpointer=None,
) -> StateGraph:
    """
    Create a GitLab Agent with LangGraph StateGraph.

    The agent workflow:
    1. Classify question (simple vs complex)
    2. For simple: direct RAG → answer
    3. For complex: plan → execute steps → refine → synthesize

    Args:
        collection_name: Name of the vector store collection.
        checkpointer: Optional LangGraph checkpointer for state persistence.

    Returns:
        Compiled LangGraph StateGraph.
    """
    logger.info(f"Creating GitLab Agent for collection: {collection_name}")

    # Create graph
    graph = StateGraph(AgentState)

    # Bind collection_name to nodes that need it
    simple_rag_bound = partial(simple_rag, collection_name=collection_name)
    execute_step_bound = partial(execute_step, collection_name=collection_name)

    # Add nodes
    graph.add_node("classify_question", classify_question)
    graph.add_node("simple_rag", simple_rag_bound)
    graph.add_node("planner", planner)
    graph.add_node("execute_step", execute_step_bound)
    graph.add_node("refine_plan", refine_plan)
    graph.add_node("synthesize_answer", synthesize_answer)

    # Set entry point
    graph.set_entry_point("classify_question")

    # Add conditional edges from classification
    graph.add_conditional_edges(
        "classify_question",
        route_by_complexity,
        {
            "simple": "simple_rag",
            "complex": "planner",
        },
    )

    # Simple path ends
    graph.add_edge("simple_rag", END)

    # Complex path: planner → execute loop → refine → synthesize
    graph.add_edge("planner", "execute_step")

    # Execute step routing
    graph.add_conditional_edges(
        "execute_step",
        route_after_execute,
        {
            "execute": "execute_step",
            "refine": "refine_plan",
        },
    )

    # Refine plan routing
    graph.add_conditional_edges(
        "refine_plan",
        route_after_refine,
        {
            "execute": "execute_step",
            "synthesize": "synthesize_answer",
        },
    )

    # Synthesize ends
    graph.add_edge("synthesize_answer", END)

    # Compile
    if checkpointer:
        compiled = graph.compile(checkpointer=checkpointer)
    else:
        compiled = graph.compile()

    return compiled


# =============================================================================
# RUN AGENT
# =============================================================================


async def run_gitlab_agent(
    agent,
    question: str,
    thread_id: Optional[str] = None,
) -> tuple[str, List[str], List[str]]:
    """
    Run the GitLab Agent with a question.

    Args:
        agent: The compiled LangGraph agent.
        question: User's question.
        thread_id: Optional thread ID for conversation tracking.

    Returns:
        Tuple of (final_answer, retrieved_docs, diagrams).
    """
    # Initialize state
    initial_state: AgentState = {
        "question": question,
        "question_type": "simple",
        "plan": [],
        "current_step_index": 0,
        "retrieved_docs": [],
        "intermediate_results": [],
        "diagrams": [],
        "final_answer": "",
        "iterations": 0,
        "max_iterations": 3,
        "current_action": None,
    }

    # Run config
    config = {}
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await agent.ainvoke(initial_state, config=config)

        final_answer = result.get("final_answer", "Could not generate an answer.")
        retrieved_docs = result.get("retrieved_docs", [])
        diagrams = result.get("diagrams", [])

        logger.info(
            f"GitLab Agent completed. Type: {result.get('question_type')}, "
            f"Steps: {len(result.get('plan', []))}, "
            f"Diagrams: {len(diagrams)}"
        )

        return final_answer, retrieved_docs, diagrams

    except Exception as e:
        logger.error(f"Error running GitLab Agent: {e}")
        raise
