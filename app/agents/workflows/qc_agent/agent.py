"""
QC Agent for generating manual unit test cases.
"""

from uuid import UUID
from typing import Optional, List, Tuple
from pathlib import Path

from langchain.agents import create_agent
from langchain.agents.middleware import (
    TodoListMiddleware,
    SummarizationMiddleware,
    FilesystemFileSearchMiddleware,
)
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_community.agent_toolkits import FileManagementToolkit


from app.rag.llms.gemini import get_llm
from app.agents.workflows.qc_agent.prompts import QC_SYSTEM_PROMPT
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_load_skill_tool(skill_path: str):
    """
    Create a tool to load the QC skill instructions.

    Args:
        skill_path: Path to the Skill.md file.

    Returns:
        A LangChain tool for loading skills.
    """

    @tool
    def load_skill(skill_name: str = "qc") -> str:
        """
        Load the QC skill instructions from Skill.md.

        Use this tool to load detailed instructions on how to write test cases.

        Args:
            skill_name: Name of the skill to load (default: "qc")

        Returns:
            The skill content with instructions.
        """
        try:
            skill_file = Path(skill_path)

            if not skill_file.exists():
                return f"Error: Skill file not found at {skill_path}"

            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()

            return f"# QC Skill Loaded\n\n{content}"

        except Exception as e:
            logger.error(f"Error loading skill: {e}")
            return f"Error loading skill: {str(e)}"

    return load_skill


def create_qc_agent(
    collection_name: str,
    chatbot_id: UUID,
    conversation_id: Optional[UUID] = None,
    checkpointer=None,
):
    """
    Create a QC Agent using create_agent with filesystem search tools and middleware.

    The QC agent generates manual unit test cases based on specifications.
    It has access to:
    - Glob: Find files in skills/references (via FilesystemFileSearchMiddleware)
    - Grep: Search content in reference files (via FilesystemFileSearchMiddleware)
    - load_skill: Load the QC skill instructions
    - search_knowledge_base: Search project documentation
    - write_todos: Track task progress (from TodoListMiddleware)

    Args:
        collection_name: Vector store collection name for knowledge base search.
        chatbot_id: Chatbot ID.
        conversation_id: Optional conversation ID.
        checkpointer: Optional checkpointer for conversation memory.

    Returns:
        Compiled agent with skills and middleware.
    """
    logger.info("Creating QC Agent")

    # Define base path for skills
    skills_base_path = "app/agents/workflows/qc_agent/skills"
    skill_file_path = f"{skills_base_path}/skill.md"

    # Create load skill tool
    load_skill_tool = create_load_skill_tool(skill_file_path)

    # Combine all tools
    file_tools = FileManagementToolkit(
        root_dir=skills_base_path,
        selected_tools=["read_file", "list_directory"],
    ).get_tools()

    tools = [
        load_skill_tool,
        *file_tools,  # Unpack the list of file tools
    ]

    # Get LLM
    llm = get_llm()

    # Create agent with middleware
    # FilesystemFileSearchMiddleware provides Glob and Grep tools automatically
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=QC_SYSTEM_PROMPT,
        middleware=[
            # FilesystemFileSearchMiddleware(
            #     root_path=skills_base_path
            # ),  # Provides Glob and Grep tools
            # TodoListMiddleware(),  # Provides write_todos tool
            # SummarizationMiddleware(
            #     model=llm,
            #     trigger=("tokens", 4000),
            #     keep=("messages", 20),
            # ),
        ],
        checkpointer=checkpointer,
    )

    logger.info("QC Agent created successfully")
    return agent


async def run_qc_agent(
    agent,
    specification: str,
    thread_id: Optional[str] = None,
) -> Tuple[str, List]:
    """
    Run the QC Agent with a specification to generate test cases.

    Args:
        agent: The compiled QC agent.
        specification: Feature specification to generate test cases for.
        thread_id: Optional thread ID for conversation tracking.

    Returns:
        Tuple of (test_cases_markdown, todos)
    """
    logger.info(f"Running QC Agent with specification: {specification[:100]}...")

    # Wrap input in HumanMessage
    messages = [
        HumanMessage(
            content=f"Generate manual unit test cases for the following specification:\n\n{specification}"
        )
    ]

    # Configure thread for checkpointing
    config = {}
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}

    # Invoke the agent
    result = await agent.ainvoke({"messages": messages}, config=config)

    # Extract response content
    response_messages = result.get("messages", [])
    test_cases = ""
    if response_messages:
        last_msg = response_messages[-1]
        test_cases = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    # Extract todos from middleware state if available
    todos = result.get("todos", [])

    logger.info(
        f"QC Agent completed. Generated {len(test_cases)} characters of test cases"
    )
    return test_cases, todos
