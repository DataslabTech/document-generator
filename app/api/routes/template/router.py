"""Роутер для `/templates`."""

import fastapi

from app.api.routes.template import template, template_version

router = fastapi.APIRouter()
router.include_router(template.router, prefix="/templates", tags=["Шаблони"])
router.include_router(
    template_version.router,
    prefix="/templates/{template_uuid}",
    tags=["Версії шаблону"],
)
