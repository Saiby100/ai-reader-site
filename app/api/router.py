from __future__ import annotations

from fastapi import APIRouter

from .routes import capabilities, health, parse

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(capabilities.router)
api_router.include_router(parse.router)
