from __future__ import annotations

from fastapi import APIRouter

from ...config import settings
from ...models import CapabilitiesResponse

router = APIRouter()


@router.get("/capabilities")
async def capabilities() -> CapabilitiesResponse:
    return CapabilitiesResponse(
        allowed_extensions=sorted(settings.allowed_extensions_set),
        max_file_size_mb=settings.max_file_size_mb,
    )
