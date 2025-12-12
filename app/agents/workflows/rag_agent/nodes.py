"""
Nodes for RAG Agent LangGraph workflow.

This module contains all the node functions that process state
in the LangGraph workflow.
"""

import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langsmith.wrappers import wrap_gemini
from langchain_core.messages.ai import AIMessage

from app.core.config import settings
from app.core.logging import get_logger
from app.agents.workflows.rag_agent.state import QAState
from app.agents.workflows.rag_agent.prompts import (
    CLASSIFY_PROMPT,
    PLANNER_PROMPT,
    VALIDATE_PLAN_PROMPT,
    STEP_REASONING_PROMPT,
    EVALUATE_PROGRESS_PROMPT,
    AGGREGATE_ANSWER_PROMPT,
)
from app.rag.vectorstores.s3_store import get_vector_store

logger = get_logger(__name__)


def get_llm(model_name: str = "gemini-2.5-flash-lite") -> ChatGoogleGenerativeAI:
    """Get a configured LLM instance."""
    return wrap_gemini(
        ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.google_api_key,
            temperature=0.7,
            verbose=True,
        )
    )


def safe_json_parse(text: str) -> dict:
    """Safely parse JSON from LLM response, handling markdown code blocks."""
    # Extract JSON from markdown code blocks if present
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if json_match:
        text = json_match.group(1)

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}


# =============================================================================
# NODE: classify_question
# =============================================================================


def classify_question(state: QAState) -> QAState:
    """
    Classify the user's question as simple or complex.

    Simple questions can be answered with a single RAG retrieval.
    Complex questions require multi-step planning and execution.
    """
    logger.info(f"Classifying question: {state['question'][:100]}...")

    llm = get_llm()
    prompt = CLASSIFY_PROMPT.format(question=state["question"])

    response = llm.invoke([HumanMessage(content=prompt)])
    classification = response.content.strip().lower()

    logger.info(f"Classification: {classification}")
    # Normalize classification
    if "complex" in classification:
        mode = "complex"
        # Initialize complex path state
        return {
            **state,
            "mode": mode,
            "plan": [],
            "current_step_index": 0,
            "step_results": [],
            "working_context": [],
            "needs_plan_refine": False,
            "done": False,
            "iterations": 0,
            "max_iterations": 3,
        }
    else:
        mode = "simple"
        return {
            **state,
            "mode": mode,
        }


# =============================================================================
# FACTORY: create_simple_qa_agent (creates node with bound context)
# =============================================================================


def create_simple_qa_agent(
    collection_name: str,
    chatbot_id,
    conversation_id,
    checkpointer=None,
):
    """
    Factory function to create simple_qa_node with bound context.

    This uses closure pattern to bind checkpointer and other context
    at graph creation time, allowing the node to access them during execution.

    Args:
        collection_name: Vector store collection name.
        chatbot_id: Chatbot UUID for document lookups.
        conversation_id: Conversation UUID for document lookups.
        checkpointer: LangGraph checkpointer for chat history persistence.

    Returns:
        Async node function with bound context.
    """
    from app.agents.workflows import rag_agent_legacy

    async def simple_qa_node(state: QAState) -> QAState:
        """
        Handle simple questions using the legacy ReAct agent.

        This node uses the legacy rag_agent with full tool-calling capability
        (search, check, summarize) without multi-step planning.
        """
        logger.info("Executing SimpleQANode with legacy ReAct agent...")

        if not collection_name:
            return {
                **state,
                "final_answer": "Error: collection_name not provided.",
                "sources": [],
            }

        # Get thread_id from state for chat history tracking
        thread_id = state.get("thread_id", "simple_qa_default")

        try:
            # Create legacy agent with checkpointer (bound via closure)
            agent = rag_agent_legacy.create_rag_agent(
                collection_name=collection_name,
                chatbot_id=chatbot_id,
                conversation_id=conversation_id,
                checkpointer=checkpointer,  # ✅ Now has checkpointer!
            )

            # Run agent with question using thread_id from state
            response_text, sources = await rag_agent_legacy.run_agent(
                agent=agent,
                message=state["question"],
                thread_id=thread_id,
            )

            return {
                **state,
                "final_answer": response_text,
                "sources": sources,
                "messages": [AIMessage(content=response_text)],
            }

        except Exception as e:
            logger.error(f"Error in SimpleQANode: {e}")
            return {
                **state,
                "final_answer": f"Error processing question: {str(e)}",
                "sources": [],
            }

    return simple_qa_node


# =============================================================================
# NODE: plan_question
# =============================================================================


def plan_question(state: QAState) -> QAState:
    """Create a multi-step execution plan for complex questions."""
    logger.info("Creating execution plan for complex question...")

    llm = get_llm()
    prompt = PLANNER_PROMPT.format(question=state["question"])

    response = llm.invoke([HumanMessage(content=prompt)])

    # Parse JSON plan from response
    parsed = safe_json_parse(response.content)
    steps = parsed.get("steps", [])

    if not steps:
        # Fallback: create a simple 2-step plan
        steps = [
            f"Step 1: Tìm kiếm thông tin liên quan đến: {state['question']}",
            "Step 2: Phân tích và tổng hợp kết quả",
        ]

    logger.info(f"Created plan with {len(steps)} steps")

    return {
        **state,
        "plan": steps,
        "current_step_index": 0,
        "needs_plan_refine": False,
        "iterations": state.get("iterations", 0),
    }


# =============================================================================
# NODE: validate_or_refine_plan
# =============================================================================


def validate_or_refine_plan(state: QAState) -> QAState:
    """Validate plan and refine if necessary."""
    logger.info("Validating plan...")

    # Skip validation if max iterations reached
    if state.get("iterations", 0) >= state.get("max_iterations", 3):
        logger.info("Max iterations reached, skipping validation")
        return {**state, "needs_plan_refine": False}

    llm = get_llm()
    plan_text = "\n".join(state.get("plan", []))
    prompt = VALIDATE_PLAN_PROMPT.format(question=state["question"], plan=plan_text)

    response = llm.invoke([HumanMessage(content=prompt)])
    parsed = safe_json_parse(response.content)

    if parsed.get("need_refine", False):
        new_plan = parsed.get("new_plan", state.get("plan", []))
        logger.info(f"Plan refined: {parsed.get('reason', 'No reason')}")
        return {
            **state,
            "plan": new_plan,
            "needs_plan_refine": True,
            "iterations": state.get("iterations", 0) + 1,
        }
    else:
        logger.info("Plan validated, proceeding with execution")
        return {**state, "needs_plan_refine": False}


# =============================================================================
# NODE: execute_step
# =============================================================================


def execute_step(state: QAState) -> QAState:
    """
    Execute the current step in the plan.
    Uses vector store search and LLM reasoning.
    """
    current_index = state.get("current_step_index", 0)
    plan = state.get("plan", [])

    if current_index >= len(plan):
        logger.info("All steps completed")
        return state

    step_instruction = plan[current_index]
    logger.info(f"Executing step {current_index + 1}: {step_instruction}")

    collection_name = state.get("collection_name", "")

    # 1) Build search query from step + question
    search_query = f"{state['question']}\n\nCurrent step: {step_instruction}"

    # 2) Retrieve relevant documents
    if collection_name:
        vector_store = get_vector_store(collection_name)
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": 10, "score_threshold": 0.6},
        )
        docs = retriever.invoke(search_query)
    else:
        docs = []

    # Format context
    if docs:
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            context_parts.append(
                f"[Document {i}] (Source: {source})\n{doc.page_content}"
            )
        context = "\n\n---\n\n".join(context_parts)
    else:
        context = "Không tìm thấy tài liệu liên quan."

    # 3) Generate step result with LLM
    llm = get_llm()
    previous_results = "\n\n".join(state.get("step_results", [])) or "Chưa có"

    prompt = STEP_REASONING_PROMPT.format(
        question=state["question"],
        step_instruction=step_instruction,
        context=context,
        previous_results=previous_results,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    step_result = (
        f"**Step {current_index + 1}:** {step_instruction}\n\n{response.content}"
    )

    # 4) Update state
    new_step_results = state.get("step_results", []) + [step_result]
    new_working_context = state.get("working_context", []) + docs

    return {
        **state,
        "step_results": new_step_results,
        "working_context": new_working_context,
        "current_step_index": current_index + 1,
    }


# =============================================================================
# NODE: evaluate_progress
# =============================================================================


def evaluate_progress(state: QAState) -> QAState:
    """Evaluate if enough information has been gathered or if plan needs refinement."""
    logger.info(
        f"Evaluating progress (step {state.get('current_step_index', 0)}/{len(state.get('plan', []))})"
    )

    # Check if max iterations reached
    if state.get("iterations", 0) >= state.get("max_iterations", 3):
        logger.info("Max iterations reached, marking done")
        return {**state, "done": True, "needs_plan_refine": False}

    llm = get_llm()
    plan_text = "\n".join(state.get("plan", []))
    step_results_text = "\n\n".join(state.get("step_results", [])) or "Chưa có"

    prompt = EVALUATE_PROGRESS_PROMPT.format(
        question=state["question"],
        plan=plan_text,
        current_step_index=state.get("current_step_index", 0),
        step_results=step_results_text,
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    parsed = safe_json_parse(response.content)

    done = parsed.get("done", False)
    needs_refine = parsed.get("need_refine_plan", False)

    logger.info(
        f"Evaluation: done={done}, need_refine={needs_refine}, reason={parsed.get('reason', '')}"
    )

    return {
        **state,
        "done": done,
        "needs_plan_refine": needs_refine,
        "iterations": state.get("iterations", 0) + 1,
    }


# =============================================================================
# NODE: aggregate_and_answer
# =============================================================================


def aggregate_and_answer(state: QAState) -> QAState:
    """Combine all step results into a comprehensive final answer."""
    logger.info("Aggregating results into final answer...")

    llm = get_llm()
    step_results_text = (
        "\n\n---\n\n".join(state.get("step_results", [])) or "Không có kết quả"
    )

    prompt = AGGREGATE_ANSWER_PROMPT.format(
        question=state["question"],
        step_results=step_results_text,
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        **state,
        "final_answer": response.content,
    }
