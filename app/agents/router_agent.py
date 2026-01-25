"""Router agent for orchestrating and dispatching tasks.

This module implements a Supervisor Agent that uses LangChain's create_agent
to route questions to the appropriate agent (GitLab Agent or RAG Agent).

Uses LangChain 1.0.0 create_agent (LangGraph-backed) pattern.
"""

from typing import Optional, Tuple, List, Any
from uuid import UUID

from langchain_aws.chat_models.bedrock_converse import ChatBedrockConverse
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from app.core.config import settings
from app.core.logging import get_logger
from app.agents.workflows.gitlab_agent import create_gitlab_agent, run_gitlab_agent
from app.agents.workflows.rag_agent import create_rag_agent, run_rag_agent

logger = get_logger(__name__)


# =============================================================================
# LLM CONFIGURATION
# =============================================================================


def get_llm(model_name: str = "amazon.nova-lite-v1:0") -> ChatBedrockConverse:
    """Get a configured LLM instance."""
    return ChatBedrockConverse(
        model=model_name,
        temperature=0,
        max_tokens=None,
        region_name="us-east-1",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


# =============================================================================
# SUPERVISOR PROMPT
# =============================================================================


SUPERVISOR_SYSTEM_PROMPT = """You are a supervisor that coordinates specialized agents to answer user questions.

## Available Agents (Tools)

**gitlab_agent**: For code-related questions
- Source code, architecture, implementation details
- GitLab repositories, branches, commits, merge requests
- Code documentation, README files
- Debugging or code analysis

**rag_agent**: For document-related questions  
- General documents, PDFs, uploaded files
- Knowledge base (policies, guides, manuals)
- Non-code information retrieval

## CRITICAL RULES

1. **You MUST call at least one agent tool to answer any question.** Never answer directly without calling an agent.

2. **Decision Logic:**
   - Question about CODE only → Call gitlab_agent
   - Question about DOCUMENTS only → Call rag_agent
   - Question about BOTH code AND documents → Call BOTH agents, then synthesize results
   - Unclear → Call rag_agent

3. **Before calling any agent, REWRITE the question** to be self-contained because agents have NO conversation history.
   - Replace pronouns ("it", "this", "that") with actual entities
   - Include necessary context from previous messages

## Examples

**Single Agent:**
- User: "How is authentication implemented?" → Call gitlab_agent("How is authentication implemented in the codebase?")
- User: "What's our security policy?" → Call rag_agent("What is the security policy document?")

**Multiple Agents:**
- User: "Compare the login code with our security guidelines"
  → Call gitlab_agent("How is login implemented in the codebase?")
  → Call rag_agent("What are the security guidelines for login?")
  → Synthesize both responses into a unified answer

**Context Rewriting:**
- Previous: discussed "project X" → User: "What files are there?" → Call rag_agent("What files does project X have?")
- Previous: searched "security.pdf" → User: "Summarize it" → Call rag_agent("Summarize security.pdf")

## Response Format

- If you called ONE agent: Return its response directly
- If you called MULTIPLE agents: Combine results into a coherent answer that addresses all aspects of the question
"""


# =============================================================================
# TOOL WRAPPERS FOR AGENTS
# =============================================================================
#
# NOTE on checkpointer usage:
# - Sub-agents are stateless per tool call - they don't maintain conversation memory
# - Only the parent router agent uses checkpointer for overall conversation tracking
# =============================================================================


def create_gitlab_agent_tool(
    collection_name: str,
):
    """
    Create a tool that wraps the GitLab Agent.

    Args:
        collection_name: Vector store collection name for GitLab codebase.

    Returns:
        A LangChain tool for calling GitLab Agent.

    Note:
        Sub-agent is stateless per tool call.
    """
    # Pre-create agent for reuse (avoids creating new agent on every call)
    _cached_agent = None

    @tool
    async def gitlab_agent(question: str) -> str:
        """
        Query the GitLab Agent for code-related questions.

        Use this tool for questions about source code, code structure,
        GitLab repositories, commits, branches, merge requests, or
        technical documentation in a codebase.

        Args:
            question: The user's question about code or GitLab.

        Returns:
            The agent's response with relevant code information.
        """
        nonlocal _cached_agent

        try:
            logger.info(f"GitLab Agent tool called with: {question[:100]}...")

            # Create agent if not cached (no checkpointer - stateless per call)
            if _cached_agent is None:
                _cached_agent = create_gitlab_agent(
                    collection_name=collection_name,
                    checkpointer=None,
                )

            final_answer, retrieved_docs, diagrams = await run_gitlab_agent(
                agent=_cached_agent,
                question=question,
            )

            # Append diagrams if available
            result = final_answer
            if diagrams:
                result += "\n\n## Diagrams\n" + "\n\n".join(diagrams)

            return result

        except Exception as e:
            logger.error(f"Error in GitLab Agent tool: {e}")
            return f"Error querying GitLab Agent: {str(e)}"

    return gitlab_agent


def create_rag_agent_tool(
    collection_name: str,
    chatbot_id: Optional[UUID] = None,
    conversation_id: Optional[UUID] = None,
):
    """
    Create a tool that wraps the RAG Agent.

    Args:
        collection_name: Vector store collection name.
        chatbot_id: Optional chatbot ID for document lookups.
        conversation_id: Optional conversation ID.

    Returns:
        A LangChain tool for calling RAG Agent.

    Note:
        Sub-agent is stateless per tool call.
    """
    # Pre-create agent for reuse
    _cached_agent = None

    @tool
    async def rag_agent(question: str) -> str:
        """
        Query the RAG Agent for document-related questions.

        Use this tool for questions about documents, knowledge base content,
        policies, guides, manuals, or any non-code information retrieval.

        Args:
            question: The user's question about documents or knowledge base.

        Returns:
            The agent's response with relevant document information.
        """
        nonlocal _cached_agent

        try:
            logger.info(f"RAG Agent tool called with: {question[:100]}...")

            # Create agent if not cached (no checkpointer - stateless per call)
            if _cached_agent is None:
                _cached_agent = create_rag_agent(
                    chatbot_id=chatbot_id,
                    collection_name=collection_name,
                    conversation_id=conversation_id,
                    checkpointer=None,
                )

            final_answer, sources = await run_rag_agent(
                agent=_cached_agent,
                question=question,
            )

            return final_answer

        except Exception as e:
            logger.error(f"Error in RAG Agent tool: {e}")
            return f"Error querying RAG Agent: {str(e)}"

    return rag_agent


# =============================================================================
# ROUTER AGENT CREATION
# =============================================================================


def create_router_agent(
    collection_name: str,
    chatbot_id: Optional[UUID] = None,
    conversation_id: Optional[UUID] = None,
    gitlab_collection_name: Optional[str] = None,
    checkpointer=None,
):
    """
    Create a Router/Supervisor Agent that routes to GitLab or RAG agents.

    Uses LangChain 1.0.0 create_agent (LangGraph-backed) for simplicity.
    The supervisor uses LLM with tool-calling to decide which agent
    should handle the user's question.

    Args:
        collection_name: Default collection name (used for RAG agent).
        chatbot_id: Optional chatbot ID for RAG agent.
        conversation_id: Optional conversation ID for RAG agent.
        gitlab_collection_name: Collection name for GitLab agent.
                               If None, uses collection_name.
        checkpointer: Optional LangGraph checkpointer for conversation memory.

    Returns:
        Compiled agent (LangGraph-backed).
    """
    logger.info(f"Creating Router Agent with collection: {collection_name}")

    # Use same collection for both if gitlab_collection_name not specified
    gitlab_coll = gitlab_collection_name or collection_name

    # Create agent tools (sub-agents are stateless)
    tools = [
        create_gitlab_agent_tool(collection_name=gitlab_coll),
        create_rag_agent_tool(
            collection_name=collection_name,
            chatbot_id=chatbot_id,
            conversation_id=conversation_id,
        ),
    ]

    # Create LLM
    llm = get_llm()

    # Create agent using LangChain 1.0.0 create_agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=SUPERVISOR_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )

    return agent


# =============================================================================
# RUN ROUTER AGENT
# =============================================================================


async def run_router_agent(
    agent,
    question: str,
    thread_id: Optional[str] = None,
) -> Tuple[str, str, List[Any]]:
    """
    Run the Router/Supervisor Agent with a question.

    Args:
        agent: The compiled router agent.
        question: User's question.
        thread_id: Optional thread ID for conversation tracking.

    Returns:
        Tuple of (final_answer, selected_agent, sources).
        - final_answer: The response from the selected agent
        - selected_agent: Which agent was used ("gitlab" or "rag" or "unknown")
        - sources: List of sources (empty for now)
    """
    # Only pass current message - checkpointer handles history automatically
    messages = [HumanMessage(content=question)]

    # Run config with thread_id
    config = {}
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await agent.ainvoke({"messages": messages}, config=config)

        # Extract response from messages
        response_messages = result.get("messages", [])

        final_answer = ""
        selected_agent = "unknown"

        if response_messages:
            # Get the last AI message as the answer
            last_message = response_messages[-1]
            final_answer = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )

            # Detect which agent was used by checking tool calls in messages
            for msg in response_messages:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_name = tc.get("name", "")
                        if "gitlab" in tool_name.lower():
                            selected_agent = "gitlab"
                            break
                        elif "rag" in tool_name.lower():
                            selected_agent = "rag"
                            break
                    if selected_agent != "unknown":
                        break

        logger.info(
            f"Router Agent completed. Selected: {selected_agent}, "
            f"Answer length: {len(final_answer) if final_answer else 0}"
        )

        return final_answer, selected_agent, []

    except Exception as e:
        logger.error(f"Error running Router Agent: {e}")
        raise


# =============================================================================
# STREAM ROUTER AGENT
# =============================================================================


async def stream_router_agent(
    agent,
    question: str,
    thread_id: Optional[str] = None,
):
    """
    Stream responses from the Router Agent using astream_events.

    This function yields events as the agent processes the question,
    enabling real-time streaming of responses to the client.

    Args:
        agent: The compiled router agent.
        question: User's question.
        thread_id: Optional thread ID for conversation tracking.

    Yields:
        Events with type and content:
        - {"type": "token", "content": "..."}: Token from LLM response
        - {"type": "tool_start", "content": "..."}: Tool call started
        - {"type": "tool_end", "content": "..."}: Tool call completed
        - {"type": "done", "content": ""}: Stream completed
        - {"type": "error", "content": "..."}: Error occurred
    """
    # Only pass current message - checkpointer handles history automatically
    messages = [HumanMessage(content=question)]

    # Run config with thread_id
    config = {}
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}

    selected_agent = "unknown"

    try:
        async for event in agent.astream_events(
            {"messages": messages}, config=config, version="v2"
        ):
            event_type = event.get("event", "")

            # Token streaming from LLM
            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    content = chunk.content
                    # Handle case where content is a list (AWS Bedrock format)
                    if isinstance(content, list):
                        # Extract text from content blocks
                        text_parts = []
                        for item in content:
                            if isinstance(item, dict) and "text" in item:
                                text_parts.append(item["text"])
                            elif isinstance(item, str):
                                text_parts.append(item)
                        content = "".join(text_parts)

                    if content:
                        yield {"type": "token", "content": content}

            # Tool call started (e.g., calling rag_agent or gitlab_agent)
            elif event_type == "on_tool_start":
                tool_name = event.get("name", "unknown")
                logger.info(f"Tool started: {tool_name}")

                # Track which agent is being used
                if "gitlab" in tool_name.lower():
                    selected_agent = "gitlab"
                elif "rag" in tool_name.lower():
                    selected_agent = "rag"

                yield {"type": "tool_start", "content": f"🔧 Calling {tool_name}..."}

            # Tool call ended
            elif event_type == "on_tool_end":
                tool_name = event.get("name", "unknown")
                logger.info(f"Tool ended: {tool_name}")
                yield {"type": "tool_end", "content": f"✅ {tool_name} completed"}

        logger.info(f"Router Agent streaming completed. Selected: {selected_agent}")
        yield {"type": "done", "content": ""}

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield {"type": "error", "content": str(e)}


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "create_router_agent",
    "run_router_agent",
    "stream_router_agent",
    "create_gitlab_agent_tool",
    "create_rag_agent_tool",
]
