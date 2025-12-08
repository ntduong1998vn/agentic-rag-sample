"""
PostgresSaver checkpointer for LangGraph agent state persistence.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Flag to track if setup has been called
_setup_done = False


def get_connection_string() -> str:
    """Get PostgreSQL connection string for psycopg3."""
    return (
        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )


@asynccontextmanager
async def get_checkpointer() -> AsyncGenerator[AsyncPostgresSaver, None]:
    """
    Get an AsyncPostgresSaver checkpointer for LangGraph.
    
    Usage:
        async with get_checkpointer() as checkpointer:
            agent = create_rag_agent(collection_name, checkpointer=checkpointer)
            result = await run_agent(agent, message, thread_id)
    """
    global _setup_done
    
    conn_string = get_connection_string()
    
    async with AsyncPostgresSaver.from_conn_string(conn_string) as checkpointer:
        # Run setup on first use to create checkpoint tables
        if not _setup_done:
            logger.info("Setting up PostgresSaver checkpoint tables...")
            await checkpointer.setup()
            _setup_done = True
            logger.info("PostgresSaver setup complete")
        
        yield checkpointer
