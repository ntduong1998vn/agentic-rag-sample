"""
RAG Agent for chatbot conversations.

Uses LangChain 1.0.0 create_agent (LangGraph-backed) with a knowledge base retrieval tool.
"""

from typing import List, Optional
from uuid import UUID

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from app.core.config import settings
from app.core.logging import get_logger
from app.agents.tools.rag_tool import create_knowledge_base_tool
from app.agents.tools.document_check_tool import create_document_check_tool
from langsmith.wrappers import wrap_gemini

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


def create_rag_agent(
    collection_name: str,
    chatbot_id: UUID,
    conversation_id: Optional[UUID] = None,
    model_name: str = "gemini-2.5-flash-lite",
    checkpointer=None,
):
    """
    Create a RAG agent with knowledge base retrieval capability.

    Args:
        collection_name: Name of the Qdrant collection to search.
        chatbot_id: The chatbot ID for document existence checks.
        conversation_id: Optional conversation ID for conversation-specific document checks.
        model_name: Name of the LLM model to use.
        checkpointer: Optional LangGraph checkpointer for state persistence.

    Returns:
        A compiled LangGraph agent.
    """
    llm = get_llm(model_name)
    tools = [
        create_knowledge_base_tool(collection_name),
        create_document_check_tool(chatbot_id, conversation_id),
    ]

    system_message = """You are a helpful AI assistant with access to a knowledge base.
When answering questions, use the search_knowledge_base tool to find relevant information.
When the user asks about a specific document name or wants to know if a document exists, 
use the check_document_exists tool to verify its presence.
Always cite your sources when providing information from the knowledge base.
If you cannot find relevant information, say so honestly."""

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_message,
        checkpointer=checkpointer,
    )

    return agent


def get_sources_from_messages(messages: list) -> List[dict]:
    """Extract source documents from agent messages."""
    sources = []
    for msg in messages:
        if hasattr(msg, "content") and isinstance(msg.content, str):
            # Look for document citations in the response
            if "[Document" in msg.content:
                sources.append(
                    {
                        "content": msg.content,
                        "metadata": {"type": "knowledge_base_result"},
                    }
                )
    return sources


async def run_agent(
    agent,
    message: str,
    thread_id: str,
) -> tuple[str, List[dict]]:
    """
    Run the RAG agent with a message.

    When the agent is compiled with a checkpointer (e.g., PostgresSaver),
    conversation history is automatically persisted and loaded.

    Args:
        agent: The compiled LangGraph agent.
        message: User's message.
        thread_id: Thread ID for conversation tracking.

    Returns:
        Tuple of (response_text, source_documents).
    """
    # Only pass current message - checkpointer handles history automatically
    messages = [HumanMessage(content=message)]

    # Run agent with thread_id config
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = await agent.ainvoke({"messages": messages}, config=config)

        # Extract response
        response_messages = result.get("messages", [])
        if response_messages:
            last_message = response_messages[-1]
            response_text = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )
        else:
            response_text = "I apologize, but I couldn't generate a response."

        # Extract sources
        sources = get_sources_from_messages(response_messages)

        return response_text, sources

    except Exception as e:
        logger.error(f"Error running agent: {e}")
        raise
