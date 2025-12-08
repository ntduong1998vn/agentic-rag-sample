from fastapi import APIRouter

from app.api.v1.endpoints import chatbots, ingestion, conversations

api_router = APIRouter()
api_router.include_router(chatbots.router, prefix="/chatbots", tags=["chatbots"])
api_router.include_router(ingestion.router, prefix="/chatbots", tags=["ingestion"])
api_router.include_router(
    conversations.router, prefix="/chatbots", tags=["conversations"]
)
