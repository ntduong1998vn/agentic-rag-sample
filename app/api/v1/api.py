from fastapi import APIRouter

from app.api.v1.endpoints import chatbots, ingestion

api_router = APIRouter()
api_router.include_router(chatbots.router, prefix="/chatbots", tags=["chatbots"])
api_router.include_router(ingestion.router, prefix="/chatbots", tags=["ingestion"])
