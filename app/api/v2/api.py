"""V2 API Router."""

from fastapi import APIRouter

from app.api.v2.endpoints import conversations

api_router = APIRouter()
api_router.include_router(
    conversations.router, prefix="/chatbots", tags=["v2-conversations"]
)
