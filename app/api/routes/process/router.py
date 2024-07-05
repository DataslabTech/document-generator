"Роутер для `/process`"

import fastapi

from app.api.routes.process import docx

router = fastapi.APIRouter()
router.include_router(docx.router, prefix="/process")
