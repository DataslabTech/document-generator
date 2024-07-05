import contextlib
import pathlib

from fastapi import FastAPI
from starlette.middleware import cors

from app.api import metadata, router
from app.core.config import settings
from app.internal import storage, template

PROJECT_TITLE = "Document Generator"
PROJECT_DESCRIPTION = """Сервіс створений для генерації `.docx` документів
наперед визначеним шаблоном. Список підтримуваних можливостей генератора:

- Підстановка тексту в рядок
- Створення параграфів
- Вставка зображень
- Вставка формул
- Створення таблиць
- Створення списків
- Генерація QR Code"""
PROJECT_VERSION = "1.0.0"


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):

    file_storage = storage.LocalStorage()
    tmp_storage = storage.LocalStorage()
    tmp_validator = template.StorageTemplateValidator(tmp_storage)
    validator = template.StorageTemplateValidator(file_storage)
    factory = template.StorageTemplateFactory(file_storage, validator)
    cache = template.MemoryTemplateCache()
    repo = template.StorageTemplateRepository(
        file_storage, tmp_storage, tmp_validator, cache, factory
    )
    repo.setup_cache()

    yield

    file_storage.delete(pathlib.Path(settings.LOCAL_STORAGE_TMP_PATH))


app = FastAPI(
    title=PROJECT_TITLE,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    description=PROJECT_DESCRIPTION,
    version=PROJECT_VERSION,
    openapi_tags=metadata.tags_metadata,
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        cors.CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router.api_router, prefix=settings.API_PREFIX)
