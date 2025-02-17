from fastapi import APIRouter
from app.api.v1.endpoints import disentanglement

api_router = APIRouter()
api_router.include_router(
    disentanglement.router,
    prefix="/disentanglement",
    tags=["Chat disentanglement"]
) 