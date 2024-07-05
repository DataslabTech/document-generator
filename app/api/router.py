"""Кореневий router застосунку."""

import fastapi

from app.api.routes import health, process, template

api_router = fastapi.APIRouter()
api_router.include_router(health.router, tags=["Healthcheck"])
api_router.include_router(template.router)
api_router.include_router(process.router)
