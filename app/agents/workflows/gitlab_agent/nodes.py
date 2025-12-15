"""
Nodes for GitLab Agent LangGraph workflow.

This module contains all the node functions that process state
in the LangGraph workflow.
"""

from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse
import json
import re
from typing import List

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langsmith.wrappers import wrap_gemini

from app.core.config import settings
from app.core.logging import get_logger
from app.agents.workflows.gitlab_agent.state import AgentState, PlanStep
from app.agents.workflows.gitlab_agent.prompts import (
    CLASSIFY_PROMPT,
    PLANNER_PROMPT,
    REASONING_PROMPT,
    DIAGRAM_PROMPT,
    REFINE_PROMPT,
    SYNTHESIZE_PROMPT,
    SIMPLE_RAG_PROMPT,
)
from app.rag.vectorstores.s3_store import get_vector_store

logger = get_logger(__name__)


def get_llm(model_name: str = "gemini-2.5-flash-lite") -> ChatBedrockConverse:
    """Get a configured LLM instance."""
    return ChatBedrockConverse(
        model="amazon.nova-micro-v1:0",
        temperature=0,
        max_tokens=None,
        region_name="us-east-1",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


# =============================================================================
# NODE: classify_question
# =============================================================================


def classify_question(state: AgentState) -> AgentState:
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

    # Normalize classification
    if "complex" in classification:
        question_type = "complex"
    else:
        question_type = "simple"

    logger.info(f"Question classified as: {question_type}")

    return {
        **state,
        "question_type": question_type,
    }


# =============================================================================
# NODE: simple_rag
# =============================================================================


def simple_rag(state: AgentState, collection_name: str) -> AgentState:
    """
    Handle simple questions with direct RAG retrieval and answer generation.
    """
    logger.info("Executing simple RAG for question...")

    # Retrieve from vector store
    vector_store = get_vector_store(collection_name)
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 6, "score_threshold": 0.7},
    )

    docs = retriever.invoke(state["question"])

    if not docs:
        return {
            **state,
            "final_answer": "Không tìm thấy thông tin liên quan trong knowledge base.",
            "retrieved_docs": [],
        }

    # Format context
    context = "\n\n---\n\n".join(
        [f"[Document {i+1}]\n{doc.page_content}" for i, doc in enumerate(docs)]
    )

    # Generate answer
    llm = get_llm()
    prompt = SIMPLE_RAG_PROMPT.format(context=context, question=state["question"])

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        **state,
        "final_answer": response.content,
        "retrieved_docs": [doc.page_content for doc in docs],
    }


# =============================================================================
# NODE: planner
# =============================================================================


def planner(state: AgentState) -> AgentState:
    """
    Create a multi-step execution plan for complex questions.
    """
    logger.info("Creating execution plan for complex question...")

    llm = get_llm()
    prompt = PLANNER_PROMPT.format(question=state["question"])

    response = llm.invoke([HumanMessage(content=prompt)])

    # Parse JSON plan from response
    try:
        # Extract JSON from response (handle markdown code blocks)
        content = response.content
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if json_match:
            content = json_match.group(1)

        plan_data = json.loads(content.strip())

        # Convert to PlanStep format
        plan: List[PlanStep] = []
        for step in plan_data:
            plan.append(
                PlanStep(
                    step_id=step["step_id"],
                    action=step["action"],
                    description=step["description"],
                    query=step["query"],
                    status="pending",
                    result=None,
                )
            )

        logger.info(f"Created plan with {len(plan)} steps")

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse plan: {e}")
        # Fallback: create a simple retrieve + reason plan
        plan = [
            PlanStep(
                step_id=1,
                action="retrieve",
                description="Search for relevant information",
                query=state["question"],
                status="pending",
                result=None,
            ),
            PlanStep(
                step_id=2,
                action="reason",
                description="Analyze and synthesize answer",
                query="Synthesize answer from retrieved information",
                status="pending",
                result=None,
            ),
        ]

    return {
        **state,
        "plan": plan,
        "current_step_index": 0,
        "iterations": 0,
        "max_iterations": 3,
    }


# =============================================================================
# NODE: execute_step
# =============================================================================


def execute_step(state: AgentState, collection_name: str) -> AgentState:
    """
    Execute the current step in the plan.

    Routes to appropriate action: retrieve, reason, or diagram.
    """
    current_index = state["current_step_index"]
    plan = state["plan"]

    if current_index >= len(plan):
        # All steps completed
        return {**state, "current_action": "done"}

    current_step = plan[current_index]
    action = current_step["action"]

    logger.info(
        f"Executing step {current_step['step_id']}: {action} - {current_step['description']}"
    )

    # Mark step as in progress
    plan[current_index] = {**current_step, "status": "in_progress"}

    # Execute based on action type
    if action == "retrieve":
        result = _execute_retrieve(current_step, collection_name)
        retrieved_docs = state.get("retrieved_docs", []) + [result]
    else:
        retrieved_docs = state.get("retrieved_docs", [])
        result = ""

    if action == "reason":
        result = _execute_reason(current_step, state)
        intermediate_results = state.get("intermediate_results", []) + [result]
    else:
        intermediate_results = state.get("intermediate_results", [])

    if action == "diagram":
        result = _execute_diagram(current_step, state)
        diagrams = state.get("diagrams", []) + [result]
    else:
        diagrams = state.get("diagrams", [])

    # Mark step as completed
    plan[current_index] = {**current_step, "status": "completed", "result": result}

    return {
        **state,
        "plan": plan,
        "current_step_index": current_index + 1,
        "retrieved_docs": retrieved_docs,
        "intermediate_results": intermediate_results,
        "diagrams": diagrams,
        "current_action": action,
    }


def _execute_retrieve(step: PlanStep, collection_name: str) -> str:
    """Execute a retrieval step."""
    vector_store = get_vector_store(collection_name)
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={"k": 6, "score_threshold": 0.7},
    )

    docs = retriever.invoke(step["query"])

    if not docs:
        return f"No documents found for query: {step['query']}"

    return "\n\n---\n\n".join(
        [f"[Document {i+1}]\n{doc.page_content}" for i, doc in enumerate(docs)]
    )


def _execute_reason(step: PlanStep, state: AgentState) -> str:
    """Execute a reasoning step."""
    llm = get_llm()

    context = "\n\n".join(state.get("retrieved_docs", []))
    previous_results = "\n\n".join(state.get("intermediate_results", []))

    prompt = REASONING_PROMPT.format(
        context=context,
        previous_results=previous_results if previous_results else "None yet",
        task_description=step["description"],
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def _execute_diagram(step: PlanStep, state: AgentState) -> str:
    """Execute a diagram generation step."""
    llm = get_llm()

    context = "\n\n".join(state.get("retrieved_docs", []))
    previous_results = "\n\n".join(state.get("intermediate_results", []))

    prompt = DIAGRAM_PROMPT.format(
        context=context,
        previous_results=previous_results if previous_results else "None",
        diagram_description=step["description"],
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


# =============================================================================
# NODE: refine_plan
# =============================================================================


def refine_plan(state: AgentState) -> AgentState:
    """
    Evaluate execution results and decide whether to continue, modify, or complete.
    """
    logger.info(f"Refining plan (iteration {state['iterations'] + 1})...")

    # Check if max iterations reached
    if state["iterations"] >= state["max_iterations"]:
        logger.info("Max iterations reached, moving to synthesis")
        return {**state, "current_action": "complete"}

    # Check if all steps completed
    pending_steps = [s for s in state["plan"] if s["status"] == "pending"]
    if not pending_steps:
        logger.info("All steps completed, moving to synthesis")
        return {**state, "current_action": "complete"}

    # Use LLM to evaluate if plan needs refinement
    llm = get_llm()

    completed_steps = [
        f"Step {s['step_id']}: {s['description']} -> {s['result'][:200] if s['result'] else 'No result'}..."
        for s in state["plan"]
        if s["status"] == "completed"
    ]

    remaining_steps = [
        f"Step {s['step_id']}: {s['action']} - {s['description']}"
        for s in state["plan"]
        if s["status"] == "pending"
    ]

    prompt = REFINE_PROMPT.format(
        question=state["question"],
        plan=json.dumps(state["plan"], indent=2, ensure_ascii=False),
        results="\n".join(state.get("retrieved_docs", [])[-2:]),  # Last 2 results
        completed_steps="\n".join(completed_steps),
        remaining_steps="\n".join(remaining_steps),
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        # Parse decision
        content = response.content
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if json_match:
            content = json_match.group(1)

        decision_data = json.loads(content.strip())
        decision = decision_data.get("decision", "continue")

        logger.info(f"Refinement decision: {decision}")

        if decision == "complete":
            return {**state, "current_action": "complete", "iterations": state["iterations"] + 1}
        elif decision == "modify" and "modified_remaining_steps" in decision_data:
            # Update remaining steps in plan
            # For simplicity, we'll keep the existing plan and just continue
            pass

        return {
            **state,
            "current_action": "continue",
            "iterations": state["iterations"] + 1,
        }

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to parse refinement decision: {e}")
        # Default: continue if there are pending steps
        if pending_steps:
            return {**state, "current_action": "continue", "iterations": state["iterations"] + 1}
        return {**state, "current_action": "complete", "iterations": state["iterations"] + 1}


# =============================================================================
# NODE: synthesize_answer
# =============================================================================


def synthesize_answer(state: AgentState) -> AgentState:
    """
    Combine all gathered information into a comprehensive final answer.
    """
    logger.info("Synthesizing final answer...")

    llm = get_llm()

    retrieved_docs = "\n\n---\n\n".join(state.get("retrieved_docs", []))
    analysis_results = "\n\n---\n\n".join(state.get("intermediate_results", []))
    diagrams = "\n\n".join(state.get("diagrams", []))

    prompt = SYNTHESIZE_PROMPT.format(
        question=state["question"],
        retrieved_docs=retrieved_docs if retrieved_docs else "None",
        analysis_results=analysis_results if analysis_results else "None",
        diagrams=diagrams if diagrams else "None",
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        **state,
        "final_answer": response.content,
    }
