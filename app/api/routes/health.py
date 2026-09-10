from __future__ import annotations

from fastapi import APIRouter

from ...parser import is_model_loaded

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "model_loaded": is_model_loaded()}
