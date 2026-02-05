"""
Sub-agent tool wrapper factories for the Supervisor Agent.

Each factory creates a LangChain tool that wraps a specialized sub-agent.
Tools use asyncio.Lock for thread-safe agent caching.
"""

import asyncio
from pathlib import Path
from typing import Optional
from uuid import UUID

from langchain_core.tools import tool

from app.core.logging import get_logger
from app.agents.workflows.gitlab_agent import create_gitlab_agent, run_gitlab_agent
from app.agents.workflows.rag_agent import create_rag_agent, run_rag_agent
from app.agents.workflows.ba_agent import create_ba_agent, run_ba_agent
from app.agents.workflows.qc_agent import create_qc_agent, run_qc_agent

logger = get_logger(__name__)


# =============================================================================
# SUB-AGENT TOOL FACTORIES
# =============================================================================


def create_gitlab_agent_tool(collection_name: str):
    """Create a thread-safe tool wrapping the GitLab Agent."""
    _cached_agent = None
    _lock = asyncio.Lock()

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

            async with _lock:
                if _cached_agent is None:
                    _cached_agent = create_gitlab_agent(
                        collection_name=collection_name,
                        checkpointer=None,
                    )

            final_answer, retrieved_docs, diagrams = await run_gitlab_agent(
                agent=_cached_agent,
                question=question,
            )

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
    """Create a thread-safe tool wrapping the RAG Agent."""
    _cached_agent = None
    _lock = asyncio.Lock()

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

            async with _lock:
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


def create_ba_agent_tool(
    collection_name: str,
    chatbot_id: UUID,
    conversation_id: Optional[UUID] = None,
):
    """Create a thread-safe tool wrapping the BA Agent."""
    _cached_agent = None
    _lock = asyncio.Lock()

    @tool
    async def ba_agent(specification: str) -> str:
        """
        Query the BA Agent for requirement analysis, impact analysis, or gap analysis.

        Use this tool for analyzing new features, raw specifications, or when
        asked to perform impact/gap analysis on the system.

        Args:
            specification: The raw specification or requirement to analyze.

        Returns:
            The agent's comprehensive BA report.
        """
        nonlocal _cached_agent

        try:
            logger.info(f"BA Agent tool called with: {specification[:100]}...")

            async with _lock:
                if _cached_agent is None:
                    _cached_agent = create_ba_agent(
                        chatbot_id=chatbot_id,
                        collection_name=collection_name,
                        conversation_id=conversation_id,
                        checkpointer=None,
                    )

            final_answer, todos = await run_ba_agent(
                agent=_cached_agent,
                raw_spec=specification,
            )

            return final_answer

        except Exception as e:
            logger.error(f"Error in BA Agent tool: {e}")
            return f"Error querying BA Agent: {str(e)}"

    return ba_agent


def create_qc_agent_tool(
    collection_name: str,
    chatbot_id: UUID,
    conversation_id: Optional[UUID] = None,
):
    """Create a thread-safe tool wrapping the QC Agent."""
    _cached_agent = None
    _lock = asyncio.Lock()

    @tool
    async def qc_agent(specification: str) -> str:
        """
        Query the QC Agent to generate manual unit test cases.

        Use this tool when the user asks to write unit tests, create test cases,
        or generate test scenarios. The agent will create comprehensive test case
        tables for QA testers.

        Args:
            specification: Detailed feature specification for generating test cases.

        Returns:
            Manual test cases in tabular markdown format.
        """
        nonlocal _cached_agent

        try:
            logger.info(f"QC Agent tool called with: {specification[:100]}...")

            async with _lock:
                if _cached_agent is None:
                    _cached_agent = create_qc_agent(
                        chatbot_id=chatbot_id,
                        collection_name=collection_name,
                        conversation_id=conversation_id,
                        checkpointer=None,
                    )

            test_cases, todos = await run_qc_agent(
                agent=_cached_agent,
                specification=specification,
            )

            return test_cases

        except Exception as e:
            logger.error(f"Error in QC Agent tool: {e}")
            return f"Error generating test cases: {str(e)}"

    return qc_agent


def create_load_skill_tool():
    """
    Create a tool to load supervisor skills by name.

    Skills are stored in app/agents/skills/ directory.
    """

    @tool
    def load_skill(skill_name: str) -> str:
        """
        Load a specialized skill prompt for the supervisor agent.

        Available skills:
        - test_request_evaluation_skill: Evaluate test case request completeness

        Args:
            skill_name: Name of the skill to load (without .md extension)

        Returns:
            The skill's prompt and context.
        """
        try:
            skills_dir = Path("app/agents/skills")
            skill_file = skills_dir / f"{skill_name}.md"

            if not skill_file.exists():
                available = [f.stem for f in skills_dir.glob("*.md")]
                return f"Error: Skill '{skill_name}' not found. Available skills: {', '.join(available)}"

            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()

            return f"# Skill Loaded: {skill_name}\n\n{content}"

        except Exception as e:
            logger.error(f"Error loading skill '{skill_name}': {e}")
            return f"Error loading skill: {str(e)}"

    return load_skill


# =============================================================================
# AGENT EXECUTOR HELPER
# =============================================================================


def create_all_tools(
    collection_name: str,
    chatbot_id: Optional[UUID] = None,
    conversation_id: Optional[UUID] = None,
    gitlab_collection_name: Optional[str] = None,
) -> dict:
    """
    Create all sub-agent tools and return them as a name→tool dict.

    Args:
        collection_name: Default collection name for RAG/BA/QC agents.
        chatbot_id: Optional chatbot ID.
        conversation_id: Optional conversation ID.
        gitlab_collection_name: Collection for GitLab agent (defaults to collection_name).

    Returns:
        Dict mapping agent short names to tool callables.
    """
    gitlab_coll = gitlab_collection_name or collection_name

    return {
        "gitlab": create_gitlab_agent_tool(collection_name=gitlab_coll),
        "ba": create_ba_agent_tool(
            collection_name=collection_name,
            chatbot_id=chatbot_id,
            conversation_id=conversation_id,
        ),
        "qc": create_qc_agent_tool(
            collection_name=collection_name,
            chatbot_id=chatbot_id,
            conversation_id=conversation_id,
        ),
    }


def create_agent_executor(tools: dict):
    """
    Return an async function that calls the right agent tool by name.

    Args:
        tools: Dict mapping agent names to tool callables.

    Returns:
        Async function (agent_name, input_text) → str.
    """

    async def execute(agent_name: str, input_text: str) -> str:
        agent_tool = tools.get(agent_name)
        if agent_tool is None:
            return f"Error: Unknown agent '{agent_name}'. Available: {list(tools.keys())}"
        return await agent_tool.ainvoke(input_text)

    return execute
