from fastapi import APIRouter

from app.api.v1 import ai, auth, data, discovery, goals, reviews, settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(reviews.router)
api_router.include_router(goals.router)
api_router.include_router(discovery.router)
api_router.include_router(data.router)
api_router.include_router(settings.router)
api_router.include_router(ai.router)
