import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.infrastructure.database.database import get_db, Base
from app.infrastructure.database.models import ChatbotModel

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def setup_database():
    import asyncio
    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def _teardown():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    asyncio.run(_setup())
    yield
    asyncio.run(_teardown())

client = TestClient(app)

def test_create_chatbot(setup_database):
    response = client.post(
        "/chatbots/",
        json={
            "name": "Test Bot",
            "model_name": "gemini-pro",
            "llm_config": {"temperature": 0.7}
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Bot"
    assert data["model_name"] == "gemini-pro"
    assert data["llm_config"] == {"temperature": 0.7}
    assert "id" in data

def test_list_chatbots(setup_database):
    # Create a chatbot first
    client.post(
        "/chatbots/",
        json={
            "name": "Bot 1",
            "model_name": "model-1",
            "llm_config": {}
        }
    )
    client.post(
        "/chatbots/",
        json={
            "name": "Bot 2",
            "model_name": "model-2",
            "llm_config": {}
        }
    )

    response = client.get("/chatbots/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_get_chatbot(setup_database):
    # Create a chatbot
    create_response = client.post(
        "/chatbots/",
        json={
            "name": "Target Bot",
            "model_name": "target-model",
            "llm_config": {}
        }
    )
    chatbot_id = create_response.json()["id"]

    # Get it
    response = client.get(f"/chatbots/{chatbot_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Target Bot"
    assert data["id"] == chatbot_id

def test_update_chatbot(setup_database):
    # Create a chatbot
    create_response = client.post(
        "/chatbots/",
        json={
            "name": "Old Name",
            "model_name": "old-model",
            "llm_config": {"temp": 0.1}
        }
    )
    chatbot_id = create_response.json()["id"]

    # Update it
    response = client.put(
        f"/chatbots/{chatbot_id}",
        json={
            "name": "New Name",
            "llm_config": {"temp": 0.9}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["model_name"] == "old-model" # Should remain unchanged
    assert data["llm_config"] == {"temp": 0.9}

def test_delete_chatbot(setup_database):
    # Create a chatbot
    create_response = client.post(
        "/chatbots/",
        json={
            "name": "To Delete",
            "model_name": "delete-me",
            "llm_config": {}
        }
    )
    chatbot_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/chatbots/{chatbot_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/chatbots/{chatbot_id}")
    assert get_response.status_code == 404
