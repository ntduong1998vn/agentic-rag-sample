"""
Database configuration and session management for SQLAlchemy.

This module provides the database connection, session factory, and base class
for ORM models in the infrastructure layer.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import AsyncGenerator, Generator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create async database URL (replace postgresql:// with postgresql+asyncpg://)
async_database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')

# Create async SQLAlchemy engine
async_engine = create_async_engine(
    async_database_url,
    pool_pre_ping=True,
    echo=False,  # Set to True for SQL query logging
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create sync engine for migrations and legacy code
sync_engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

# Create sync session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Create declarative base for ORM models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency for FastAPI to get database session.
    
    Yields:
        AsyncSession: SQLAlchemy async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_sync_db() -> Generator[Session, None, None]:
    """
    Sync dependency for FastAPI to get database session (legacy).
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database - create all tables.
    
    This should be called on application startup.
    """
    try:
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_all_tables() -> None:
    """
    Drop all tables - use with caution!
    
    This is primarily for testing/development purposes.
    """
    try:
        Base.metadata.drop_all(bind=sync_engine)
        logger.info("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise
