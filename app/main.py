from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .api.errors import register_error_handlers
from .api.router import api_router
from .logging import configure_logging
from .parsing import load_models

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    load_models()
    yield


app = FastAPI(title="Document Parser", lifespan=lifespan)

register_error_handlers(app)
app.include_router(api_router)
