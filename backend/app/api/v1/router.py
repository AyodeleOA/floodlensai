from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin, map, reports, system, voice

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(reports.router)
api_router.include_router(map.router)
api_router.include_router(admin.router)
api_router.include_router(voice.router)
api_router.include_router(system.router)
