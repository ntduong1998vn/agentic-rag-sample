"""
Node functions for the Supervisor (Router) Agent StateGraph.

Nodes:
- maybe_summarize: Summarize conversation history if too long
- rewrite_query: Resolve pronouns and make question self-contained
- supervisor_decide: Central brain — decide next action (with interrupt support)
- execute_agent: Call a sub-agent and store result
- synthesize_and_respond: Format final answer from agent results
"""

from langchain_core.messages import HumanMessage, AIMessage

from langgraph.types import interrupt

from app.core.logging import get_logger
from app.rag.llms.gemini import get_llm
from app.agents.router.state import (
    SupervisorState,
    SupervisorAction,
    SupervisorDecision,
)
from app.agents.router.prompts import (
    REWRITE_QUERY_PROMPT,
    SUPERVISOR_DECIDE_PROMPT,
    SYNTHESIZE_PROMPT,
)

logger = get_logger(__name__)


# =============================================================================
# NODE: maybe_summarize
# =============================================================================


async def maybe_summarize(state: SupervisorState) -> dict:
    """
    Summarize conversation history if token count exceeds threshold.

    Checks message count as a proxy for token usage. If messages are too many,
    uses LLM to create a concise summary for context.
    """
    messages = state.get("messages", [])

    # Use message count as proxy (roughly 100 tokens per message)
    # Summarize if > 40 messages (approx 4000 tokens)
    if len(messages) <= 40:
        return {}

    logger.info(f"Summarizing {len(messages)} messages...")

    # Take recent messages for summarization
    recent = messages[-40:]
    conversation_text = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content}"
        for m in recent
        if hasattr(m, "content") and m.content
    )

    llm = get_llm()
    summary_prompt = (
        "Summarize the following conversation concisely, preserving key topics, "
        "entities, decisions, and any pending questions:\n\n"
        f"{conversation_text}\n\nSummary:"
    )

    response = await llm.ainvoke([HumanMessage(content=summary_prompt)])
    summary = response.content if hasattr(response, "content") else str(response)

    logger.info(f"Conversation summarized ({len(summary)} chars)")
    return {"conversation_summary": summary}


# =============================================================================
# NODE: rewrite_query
# =============================================================================


async def rewrite_query(state: SupervisorState) -> dict:
    """
    Rewrite the user's question to be self-contained.

    Resolves pronouns and adds context from conversation history so
    sub-agents (which are stateless) can understand the question.
    """
    question = state.get("question", "")
    messages = state.get("messages", [])
    summary = state.get("conversation_summary", "")

    # If no conversation history, return question as-is
    if len(messages) <= 1 and not summary:
        return {"rewritten_question": question}

    # Format recent messages for context
    recent = messages[-10:]  # Last 10 messages
    recent_text = "\n".join(
        f"{'User' if isinstance(m, HumanMessage) else 'AI'}: {m.content[:200]}"
        for m in recent
        if hasattr(m, "content") and m.content
    )

    prompt = REWRITE_QUERY_PROMPT.format(
        conversation_summary=summary or "(No summary available)",
        recent_messages=recent_text or "(No prior messages)",
        question=question,
    )

    llm = get_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    rewritten = response.content if hasattr(response, "content") else str(response)

    # Clean up — sometimes LLM wraps in quotes
    rewritten = rewritten.strip().strip('"').strip("'")

    logger.info(f"Query rewritten: '{question[:50]}' → '{rewritten[:50]}'")
    return {"rewritten_question": rewritten}


# =============================================================================
# NODE: supervisor_decide
# =============================================================================


async def supervisor_decide(state: SupervisorState) -> dict:
    """
    Central supervisor brain — evaluate context and decide next action.

    Possible outcomes:
    - EXECUTE_AGENT: Call a sub-agent → routes to execute_agent node
    - RESPOND: Enough info to answer → routes to synthesize_and_respond
    - ASK_HUMAN: Need clarification → interrupt() pauses the graph

    When interrupt() is called, the graph pauses and the user sees the question.
    On resume, this node re-executes from the start with the user's answer
    available as the return value of interrupt().

    Note: Code before interrupt() must be idempotent since it re-runs on resume.
    """
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 5)

    # Safety: check iteration limit
    if iteration >= max_iterations:
        logger.warning(f"Max iterations ({max_iterations}) reached, forcing respond")
        agent_results = state.get("agent_results", {})
        if agent_results:
            return {
                "next_action": "respond",
                "iteration": iteration,
            }
        return {
            "final_answer": "I've reached my processing limit. Please try rephrasing your question.",
            "next_action": "respond",
            "iteration": iteration,
        }

    rewritten_question = state.get("rewritten_question", state.get("question", ""))
    original_question = state.get("question", "")
    agent_results = state.get("agent_results", {})
    selected_agents = state.get("selected_agents", [])

    # Format agent results for prompt
    if agent_results:
        results_text = "\n\n".join(
            f"### {name} agent result:\n{result[:2000]}"
            for name, result in agent_results.items()
        )
    else:
        results_text = "(No agent results yet)"

    agents_called = ", ".join(selected_agents) if selected_agents else "(None)"

    prompt = SUPERVISOR_DECIDE_PROMPT.format(
        rewritten_question=rewritten_question,
        original_question=original_question,
        agent_results=results_text,
        selected_agents=agents_called,
        iteration=iteration,
        max_iterations=max_iterations,
    )

    llm = get_llm()
    decision: SupervisorDecision = await llm.with_structured_output(
        SupervisorDecision
    ).ainvoke([HumanMessage(content=prompt)])

    logger.info(
        f"Supervisor decision (iter {iteration}): "
        f"action={decision.action}, target={decision.target_agent}, "
        f"reasoning={decision.reasoning[:100]}"
    )

    if decision.action == SupervisorAction.ASK_HUMAN:
        # INTERRUPT: pause graph and ask user for clarification
        question_text = (
            decision.clarification_question
            or "Could you provide more details about your request?"
        )

        user_response = interrupt({
            "type": "clarification",
            "question": question_text,
        })

        # Graph resumes here with user's answer as user_response
        logger.info(f"Resumed from interrupt with: {str(user_response)[:100]}")

        return {
            "question": str(user_response),
            "rewritten_question": str(user_response),
            "iteration": iteration + 1,
            "next_action": "re_decide",
            "messages": [
                AIMessage(content=question_text),
                HumanMessage(content=str(user_response)),
            ],
        }

    elif decision.action == SupervisorAction.EXECUTE_AGENT:
        return {
            "target_agent": decision.target_agent,
            "agent_input": decision.agent_input or rewritten_question,
            "iteration": iteration + 1,
            "next_action": "execute",
        }

    elif decision.action == SupervisorAction.RESPOND:
        # If supervisor provides a direct response, use it
        if decision.response:
            return {
                "final_answer": decision.response,
                "next_action": "respond",
                "iteration": iteration,
            }
        # Otherwise route to synthesize node to combine agent results
        return {
            "next_action": "respond",
            "iteration": iteration,
        }

    # Fallback
    return {
        "next_action": "respond",
        "iteration": iteration,
    }


# =============================================================================
# NODE: execute_agent
# =============================================================================


async def execute_agent(state: SupervisorState, agent_executor) -> dict:
    """
    Call a sub-agent and store the result.

    Uses the agent_executor function (bound via functools.partial in graph.py)
    to invoke the appropriate sub-agent tool.

    Args:
        state: Current supervisor state.
        agent_executor: Async callable (agent_name, input_text) → str.

    Returns:
        Updated agent_results and selected_agents.
    """
    target = state.get("target_agent", "")
    input_text = state.get("agent_input", state.get("rewritten_question", ""))

    logger.info(f"Executing agent '{target}' with input: {input_text[:100]}...")

    try:
        result = await agent_executor(target, input_text)
    except Exception as e:
        logger.error(f"Error executing agent '{target}': {e}")
        result = f"Error from {target} agent: {str(e)}"

    # Accumulate results
    agent_results = dict(state.get("agent_results", {}))
    agent_results[target] = result

    selected = list(state.get("selected_agents", []))
    selected.append(target)

    logger.info(f"Agent '{target}' completed ({len(result)} chars)")

    return {
        "agent_results": agent_results,
        "selected_agents": selected,
    }


# =============================================================================
# NODE: synthesize_and_respond
# =============================================================================


async def synthesize_and_respond(state: SupervisorState) -> dict:
    """
    Format the final answer from agent results.

    - If supervisor already set final_answer (direct respond), pass through.
    - If single agent result, return it directly.
    - If multiple agent results, use LLM to synthesize.
    """
    # Check if final_answer was already set by supervisor_decide
    existing_answer = state.get("final_answer", "")
    if existing_answer:
        return {
            "final_answer": existing_answer,
            "sources": state.get("sources", []),
        }

    agent_results = state.get("agent_results", {})
    question = state.get("rewritten_question", state.get("question", ""))

    if not agent_results:
        return {
            "final_answer": "I wasn't able to find relevant information to answer your question.",
            "sources": [],
        }

    # Single agent result — return directly
    if len(agent_results) == 1:
        agent_name, result = next(iter(agent_results.items()))
        return {
            "final_answer": result,
            "sources": [],
        }

    # Multiple agent results — synthesize with LLM
    results_text = "\n\n".join(
        f"### {name} agent:\n{result}"
        for name, result in agent_results.items()
    )

    prompt = SYNTHESIZE_PROMPT.format(
        question=question,
        agent_results=results_text,
    )

    llm = get_llm()
    response = await llm.ainvoke([HumanMessage(content=prompt)])
    synthesized = response.content if hasattr(response, "content") else str(response)

    logger.info(f"Synthesized response from {len(agent_results)} agents")

    return {
        "final_answer": synthesized,
        "sources": [],
    }
