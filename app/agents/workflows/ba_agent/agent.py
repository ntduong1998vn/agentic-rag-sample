from uuid import UUID
from typing import Optional, List, Tuple

from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware, SummarizationMiddleware
from langchain_core.messages import HumanMessage

from app.rag.llms.gemini import get_llm
from app.agents.tools.unified_search_tool import create_unified_search_tool
from app.agents.workflows.ba_agent.prompts import BA_SYSTEM_PROMPT


def create_ba_agent(
    collection_name: str,
    chatbot_id: UUID,
    conversation_id: Optional[UUID] = None,
    checkpointer=None,
):
    """
    Create a BA Agent that uses create_agent and middleware for planning.
    """
    
    # Create the unified search tool bound to the collection and chatbot
    search_tool = create_unified_search_tool(
        collection_name=collection_name,
        chatbot_id=chatbot_id,
        conversation_id=conversation_id,
    )
    
    # Instantiate the LLM
    llm = get_llm()
    
    # Create the agent using LangChain's create_agent pattern
    # This uses a ReAct workflow internally with the provided tools and prompt
    agent = create_agent(
        model=llm,
        tools=[search_tool],
        system_prompt=BA_SYSTEM_PROMPT,
        middleware=[
            TodoListMiddleware(),  # Injects write_todos tool and task tracking
            SummarizationMiddleware(
                model=llm,
                trigger=("tokens", 4000),
                keep=("messages", 20),
            ),
        ],
        checkpointer=checkpointer,
    )
    
    return agent


async def run_ba_agent(
    agent,
    raw_spec: str,
    thread_id: Optional[str] = None,
) -> Tuple[str, List]:
    """
    Run the BA Agent with the given specification.
    
    Returns:
        A tuple of (final_report, todos)
    """
    # Wrap input in HumanMessage
    messages = [HumanMessage(content=f"Analyze this specification:\n\n{raw_spec}")]
    
    # Configure thread search for checkpointing
    config = {}
    if thread_id:
        config = {"configurable": {"thread_id": thread_id}}
    
    # Invoke the agent
    result = await agent.ainvoke({"messages": messages}, config=config)
    
    # Extract response content
    response_messages = result.get("messages", [])
    final_answer = ""
    if response_messages:
        last_msg = response_messages[-1]
        final_answer = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
        
    # Extract todos from middleware state if available
    todos = result.get("todos", [])
    
    return final_answer, todos
