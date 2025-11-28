from fastapi import APIRouter

from app.api.v1.endpoints import chatbots

api_router = APIRouter()
api_router.include_router(chatbots.router, prefix="/chatbots", tags=["chatbots"])
