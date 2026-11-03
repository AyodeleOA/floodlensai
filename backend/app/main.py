from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.schemas.common import HealthLiveResponse, HealthReadyResponse

settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)

# --- Health router ---
# uvicorn app.main:app --reload
health_router = APIRouter(tags=["health"])


@health_router.get("/health/live", response_model=HealthLiveResponse)
async def health_live():
    """Liveness probe — always returns ok if the process is running."""
    return HealthLiveResponse(status="ok")


@health_router.get("/health/ready", response_model=HealthReadyResponse)
async def health_ready():
    """Readiness probe — checks database connectivity."""
    db_ok = "connected"
    try:
        from sqlalchemy import text
        from app.db.session import async_session_factory

        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning(f"Health ready DB check failed: {e}")
        db_ok = "disconnected"
    return HealthReadyResponse(status="ok" if db_ok == "connected" else "degraded", database=db_ok)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup and shutdown lifecycle."""
    logger.info("FloodLens AI starting", extra=settings.config_summary())
    yield
    logger.info("FloodLens AI shutting down")


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Community-powered flood observation, geospatial risk mapping, and decision-support for African communities.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS
    origins = settings.FRONTEND_ORIGIN.split(",") if settings.FRONTEND_ORIGIN else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router)
    app.include_router(api_router)

    return app


app = create_app()
