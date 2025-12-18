"""
RAG Agent using LangGraph StateGraph.

This agent handles document Q&A with support for both simple and complex questions.
Simple questions use embedded ReAct agent, while complex questions use multi-step
planning with refinement capabilities.
"""

from langchain_core.messages.human import HumanMessage
from typing import Optional
from uuid import UUID

from langgraph.graph import StateGraph, END

from app.core.logging import get_logger
from app.agents.workflows.rag_agent.state import QAState
from app.agents.workflows.rag_agent.nodes import (
    classify_question,
    create_simple_qa_agent,
    pre_search_node,
    plan_question,
    validate_or_refine_plan,
    execute_step,
    evaluate_progress,
    aggregate_and_answer,
)

logger = get_logger(__name__)


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================


def route_by_mode(state: QAState) -> str:
    """Route based on question classification (simple/complex)."""
    return state.get("mode", "simple")


def route_plan_validation(state: QAState) -> str:
    """Route after plan validation - refine or proceed to execution."""
    if state.get("needs_plan_refine", False):
        return "refine"
    return "ok"


def route_after_evaluate(state: QAState) -> str:
    """
    Route after progress evaluation.
    - refine_plan: Go back to planning if plan needs adjustment
    - next_step: Continue with next step if more steps remain
    - done: Move to aggregation if enough info gathered
    """
    if state.get("needs_plan_refine", False):
        return "refine_plan"

    if state.get("done", False):
        return "done"

    # Check if more steps remain
    current_index = state.get("current_step_index", 0)
    plan = state.get("plan", [])

    if current_index < len(plan):
        return "next_step"

    # All steps completed
    return "done"


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================


def create_rag_agent(
    chatbot_id: UUID,
    collection_name: str,
    conversation_id: UUID,
    checkpointer=None,
) -> StateGraph:
    """
    Create a RAG Agent with LangGraph StateGraph.

    The agent workflow:
    1. Classify question (simple vs complex)
    2. For simple: simple_qa_node (embedded ReAct agent) → END
    3. For complex: plan → validate → execute steps → evaluate → aggregate → END

    Args:
        collection_name: Name of the vector store collection.
        chatbot_id: Optional chatbot ID for document lookups.
        conversation_id: Optional conversation ID for document lookups.
        checkpointer: Optional LangGraph checkpointer for state persistence.

    Returns:
        Compiled LangGraph StateGraph.
    """
    # Create simple_qa_node with bound context via factory
    simple_qa_node = create_simple_qa_agent(
        collection_name=collection_name,
        chatbot_id=chatbot_id,
        conversation_id=conversation_id,
        checkpointer=checkpointer,
    )

    # Create graph
    graph = StateGraph(QAState)

    # Add nodes
    graph.add_node("classify_question", classify_question)
    graph.add_node("simple_qa_node", simple_qa_node)  # Factory-created node
    graph.add_node("pre_search_node", pre_search_node)  # Pre-search for complex path
    graph.add_node("plan_question", plan_question)
    graph.add_node("validate_or_refine_plan", validate_or_refine_plan)
    graph.add_node("execute_step", execute_step)
    graph.add_node("evaluate_progress", evaluate_progress)
    graph.add_node("aggregate_and_answer", aggregate_and_answer)

    # Set entry point
    graph.set_entry_point("classify_question")

    # Route: classify → simple_qa_node OR pre_search_node (for complex)
    graph.add_conditional_edges(
        "classify_question",
        route_by_mode,
        {
            "simple": "simple_qa_node",
            "complex": "pre_search_node",
        },
    )

    # Simple path: simple_qa_node → END
    graph.add_edge("simple_qa_node", END)

    # Complex path: pre_search → plan → validate
    graph.add_edge("pre_search_node", "plan_question")
    graph.add_edge("plan_question", "validate_or_refine_plan")

    # Route: validate → refine (back to plan) OR ok (proceed to execute)
    graph.add_conditional_edges(
        "validate_or_refine_plan",
        route_plan_validation,
        {
            "refine": "plan_question",
            "ok": "execute_step",
        },
    )

    # Execute → evaluate
    graph.add_edge("execute_step", "evaluate_progress")

    # Route: evaluate → refine_plan OR next_step OR done
    graph.add_conditional_edges(
        "evaluate_progress",
        route_after_evaluate,
        {
            "refine_plan": "plan_question",
            "next_step": "execute_step",
            "done": "aggregate_and_answer",
        },
    )

    # Aggregate → END
    graph.add_edge("aggregate_and_answer", END)

    # Compile
    if checkpointer:
        compiled = graph.compile(checkpointer=checkpointer)
    else:
        compiled = graph.compile()

    # Store metadata for initialization
    compiled._rag_metadata = {
        "chatbot_id": chatbot_id,
        "collection_name": collection_name,
        "conversation_id": conversation_id,
    }

    return compiled


# =============================================================================
# RUN AGENT
# =============================================================================


async def run_rag_agent(
    agent,
    question: str,
    thread_id: Optional[str] = None,
) -> tuple[str, list[dict]]:
    """
    Run the RAG Agent with a question.

    Args:
        agent: The compiled LangGraph agent.
        question: User's question.
        thread_id: Optional thread ID for conversation tracking.

    Returns:
        Tuple of (response_text, sources) for backward compatibility.
        - response_text: The final answer string
        - sources: List of source documents with content and metadata
    """
    # Get metadata from agent
    metadata = getattr(agent, "_rag_metadata", {})

    # Initialize state
    initial_state: QAState = {
        "question": question,
        "mode": "simple",  # Will be updated by classify_question
        "chatbot_id": metadata.get("chatbot_id"),
        "collection_name": metadata.get("collection_name"),
        "conversation_id": metadata.get("conversation_id"),
        "thread_id": thread_id,  # For simple_qa_node to use with legacy agent
        "messages": [HumanMessage(content=question)],
    }

    # Run config
    config = {}
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await agent.ainvoke(initial_state, config=config)

        final_answer = result.get("final_answer", "Could not generate an answer.")

        # Build sources based on path taken
        sources = []

        # For simple path: sources are directly returned by simple_qa_node
        if result.get("mode") == "simple":
            sources = result.get("sources", [])

        # For complex path: extract from working_context
        else:
            context_docs = result.get("working_context", [])
            for doc in context_docs:
                if hasattr(doc, "page_content"):
                    sources.append(
                        {
                            "content": doc.page_content,
                            "metadata": getattr(doc, "metadata", {}),
                        }
                    )

        logger.info(
            f"RAG Agent completed. Mode: {result.get('mode')}, "
            f"Steps: {len(result.get('plan', []))}, "
            f"Sources: {len(sources)}"
        )

        return final_answer, sources

    except Exception as e:
        logger.error(f"Error running RAG agent: {e}")
        raise


# Alias for backward compatibility
run_agent = run_rag_agent
