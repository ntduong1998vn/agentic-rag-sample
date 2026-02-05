"""
StateGraph construction and execution for the Supervisor (Router) Agent.

Builds the LangGraph workflow:
  maybe_summarize → rewrite_query → supervisor_decide ←──────────┐
                                         │                       │
                      ┌─────────────────┤──────────┐            │
                      ▼                 ▼          ▼            │
                execute_agent       respond   [interrupt()]     │
                      │                ▼                        │
                      │               END                       │
                      └─────────────────────────────────────────┘

Provides:
- create_router_agent(): Build and compile the StateGraph
- run_router_agent(): Single-shot invocation with interrupt handling
- stream_router_agent(): Streaming invocation with SSE-friendly events
"""

from functools import partial
from typing import Optional, Tuple, List, Any

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.types import Command

from app.core.logging import get_logger
from app.agents.router.state import SupervisorState
from app.agents.router.nodes import (
    maybe_summarize,
    rewrite_query,
    supervisor_decide,
    execute_agent,
    synthesize_and_respond,
)
from app.agents.router.tools import create_all_tools, create_agent_executor

logger = get_logger(__name__)


# =============================================================================
# ROUTING
# =============================================================================


def route_after_supervisor(state: SupervisorState) -> str:
    """Route based on supervisor's decision."""
    action = state.get("next_action", "respond")
    if action == "execute":
        return "execute_agent"
    elif action == "re_decide":
        return "supervisor_decide"  # Loop back after interrupt resume
    return "synthesize_and_respond"


# =============================================================================
# GRAPH CONSTRUCTION
# =============================================================================


def create_router_agent(
    collection_name: str,
    chatbot_id=None,
    conversation_id=None,
    gitlab_collection_name: Optional[str] = None,
    checkpointer=None,
):
    """
    Create a Supervisor Agent using LangGraph StateGraph.

    The supervisor evaluates each request, decides which sub-agent(s) to call,
    and loops until it has enough information to respond. Supports human-in-the-loop
    via LangGraph interrupt() for clarification questions.

    Args:
        collection_name: Default vector store collection name.
        chatbot_id: Optional chatbot ID for document lookups.
        conversation_id: Optional conversation ID.
        gitlab_collection_name: Collection for GitLab agent (defaults to collection_name).
        checkpointer: LangGraph checkpointer for state persistence (required for interrupt).

    Returns:
        Compiled LangGraph agent.
    """
    logger.info(f"Creating Supervisor Agent with collection: {collection_name}")

    # Create sub-agent tools
    tools = create_all_tools(
        collection_name=collection_name,
        chatbot_id=chatbot_id,
        conversation_id=conversation_id,
        gitlab_collection_name=gitlab_collection_name,
    )
    agent_executor_fn = create_agent_executor(tools)

    # Bind agent_executor to execute_agent node
    execute_bound = partial(execute_agent, agent_executor=agent_executor_fn)

    # Build graph
    graph = StateGraph(SupervisorState)

    graph.add_node("maybe_summarize", maybe_summarize)
    graph.add_node("rewrite_query", rewrite_query)
    graph.add_node("supervisor_decide", supervisor_decide)
    graph.add_node("execute_agent", execute_bound)
    graph.add_node("synthesize_and_respond", synthesize_and_respond)

    # Entry point
    graph.set_entry_point("maybe_summarize")

    # Linear: maybe_summarize → rewrite_query → supervisor_decide
    graph.add_edge("maybe_summarize", "rewrite_query")
    graph.add_edge("rewrite_query", "supervisor_decide")

    # Supervisor decision routing
    graph.add_conditional_edges(
        "supervisor_decide",
        route_after_supervisor,
        {
            "execute_agent": "execute_agent",
            "supervisor_decide": "supervisor_decide",
            "synthesize_and_respond": "synthesize_and_respond",
        },
    )

    # After executing agent → always loop back to supervisor
    graph.add_edge("execute_agent", "supervisor_decide")

    # Synthesize → END
    graph.add_edge("synthesize_and_respond", END)

    # Compile with checkpointer (required for interrupt support)
    compiled = graph.compile(checkpointer=checkpointer)

    return compiled


# =============================================================================
# RUN (single-shot with interrupt handling)
# =============================================================================


async def run_router_agent(
    agent,
    question: str,
    thread_id: Optional[str] = None,
) -> Tuple[str, str, List[Any]]:
    """
    Run the Supervisor Agent with a question.

    Handles both new invocations and resumptions after interrupt.
    When the graph is paused (waiting for user clarification), calling this
    again with the user's answer will resume the graph.

    Args:
        agent: The compiled supervisor agent.
        question: User's question (or clarification answer if resuming).
        thread_id: Thread ID for conversation tracking. Required for interrupt support.

    Returns:
        Tuple of (final_answer, selected_agents_csv, sources).
    """
    config = {}
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}

    try:
        # Check if there's a pending interrupt (user is responding to a clarification)
        is_resuming = False
        if thread_id and config:
            try:
                snapshot = await agent.aget_state(config)
                if snapshot and snapshot.next:
                    # Graph is paused at an interrupt — resume with user's answer
                    is_resuming = True
                    logger.info(f"Resuming from interrupt with: {question[:100]}...")
            except Exception:
                # No prior state — normal invocation
                pass

        if is_resuming:
            result = await agent.ainvoke(
                Command(resume=question), config=config
            )
        else:
            initial_state = {
                "question": question,
                "messages": [HumanMessage(content=question)],
                "iteration": 0,
                "max_iterations": 5,
                "agent_results": {},
                "selected_agents": [],
                "sources": [],
            }
            result = await agent.ainvoke(initial_state, config=config)

        # Check if result contains an interrupt (graph paused for clarification)
        if hasattr(result, "__getitem__") and "__interrupt__" in result:
            interrupt_info = result["__interrupt__"]
            if interrupt_info:
                interrupt_value = interrupt_info[0].value
                clarification = interrupt_value.get(
                    "question", "Could you provide more details?"
                )
                logger.info(f"Graph interrupted, asking: {clarification[:100]}")
                return clarification, "supervisor", []

        # Normal completion
        final_answer = result.get("final_answer", "")
        selected = result.get("selected_agents", [])
        selected_csv = ",".join(selected) if selected else "unknown"
        sources = result.get("sources", [])

        logger.info(
            f"Supervisor completed. Agents: {selected_csv}, "
            f"Answer length: {len(final_answer)}"
        )

        return final_answer, selected_csv, sources

    except Exception as e:
        logger.error(f"Error running Supervisor Agent: {e}")
        raise


# =============================================================================
# STREAM (SSE-friendly with interrupt support)
# =============================================================================


async def stream_router_agent(
    agent,
    question: str,
    thread_id: Optional[str] = None,
):
    """
    Stream responses from the Supervisor Agent.

    Uses astream() with stream_mode=["messages", "updates"] instead of
    astream_events() for reliable interrupt event handling.

    Yields events:
    - {"type": "token", "content": "..."}: Token from LLM
    - {"type": "tool_start", "content": "..."}: Sub-agent call started
    - {"type": "tool_end", "content": "..."}: Sub-agent call completed
    - {"type": "interrupt", "content": "..."}: Clarification question for user
    - {"type": "done", "content": ""}: Stream completed
    - {"type": "error", "content": "..."}: Error occurred

    Args:
        agent: The compiled supervisor agent.
        question: User's question (or clarification answer if resuming).
        thread_id: Thread ID for conversation tracking.

    Yields:
        Dict events for SSE streaming.
    """
    config = {}
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}

    try:
        # Detect resume vs new invocation
        input_data = None
        is_resuming = False

        if thread_id and config:
            try:
                snapshot = await agent.aget_state(config)
                if snapshot and snapshot.next:
                    is_resuming = True
                    input_data = Command(resume=question)
                    logger.info(f"Streaming resume from interrupt: {question[:100]}...")
            except Exception:
                pass

        if not is_resuming:
            input_data = {
                "question": question,
                "messages": [HumanMessage(content=question)],
                "iteration": 0,
                "max_iterations": 5,
                "agent_results": {},
                "selected_agents": [],
                "sources": [],
            }

        last_node = ""
        streamed_tokens = False

        async for chunk in agent.astream(
            input_data,
            config=config,
            stream_mode=["messages", "updates"],
        ):
            if not isinstance(chunk, tuple) or len(chunk) < 2:
                continue

            mode = chunk[0]
            data = chunk[1]

            if mode == "messages":
                msg, metadata = data
                if hasattr(msg, "content") and msg.content:
                    # Only yield tokens from the final synthesis node.
                    # supervisor_decide outputs structured JSON (SupervisorDecision),
                    # which is internal — never stream it to the user.
                    node_name = metadata.get("langgraph_node", "")
                    if node_name == "synthesize_and_respond":
                        streamed_tokens = True
                        yield {"type": "token", "content": msg.content}

            elif mode == "updates":
                if isinstance(data, dict):
                    # Check for interrupt
                    if "__interrupt__" in data:
                        interrupt_list = data["__interrupt__"]
                        if interrupt_list:
                            interrupt_val = interrupt_list[0].value
                            question_text = interrupt_val.get(
                                "question", "Could you provide more details?"
                            )
                            yield {"type": "interrupt", "content": question_text}
                            return  # Stop streaming — graph is paused

                    # Track node transitions for tool_start / tool_end events
                    for node_name, node_output in data.items():
                        if node_name == "execute_agent":
                            # Starting agent execution
                            target = ""
                            if isinstance(node_output, dict):
                                # Try to extract target from selected_agents
                                agents = node_output.get("selected_agents", [])
                                if agents:
                                    target = agents[-1]
                            yield {
                                "type": "tool_start",
                                "content": f"Calling {target or 'agent'}...",
                            }
                        elif node_name == "synthesize_and_respond":
                            # When synthesize returns final_answer without an LLM call
                            # (single agent result or direct respond), no "messages"
                            # tokens are emitted. Yield the answer from "updates" instead.
                            if isinstance(node_output, dict):
                                answer = node_output.get("final_answer", "")
                                if answer and not streamed_tokens:
                                    yield {"type": "token", "content": answer}

                        # Track last node for context
                        last_node = node_name

        yield {"type": "done", "content": ""}

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield {"type": "error", "content": str(e)}
