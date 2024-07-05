"""Модуль описує роути `/templates/{template_uuid}/versions`"""

import io
import uuid

import fastapi

from app.api import injection, schemas
from app.internal import template

router = fastapi.APIRouter()


router = fastapi.APIRouter(prefix="/versions")


@router.get(
    "/",
    response_model=list[template.schema.TemplateVersionResponse],
    summary="Список шаблонів",
)
def get_template_versions(
    template_uuid: uuid.UUID,
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):
    tpl = repo.get(template_uuid)
    if tpl is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template was not found.",
        )

    return repo.get_versions(tpl)


@router.get(
    "/{version_tag}",
    response_model=template.schema.TemplateVersionResponse,
    summary="Версія шаблону за версійним тегом",
    responses={
        404: {
            "model": schemas.HTTPError,
            "description": "Template version was not found",
            "content": {
                "application/json": {
                    "example": {"detail": ("Template version was not found")}
                }
            },
        }
    },
)
def get_template_version_by_tag(
    template_uuid: uuid.UUID,
    version_tag: str,
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):
    tpl = repo.get(template_uuid)
    if tpl is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template was not found.",
        )

    version = repo.get_version(tpl, version_tag)

    if version is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template version was not found.",
        )
    return version


@router.post(
    "/",
    response_model=template.schema.TemplateVersionResponse,
    summary="Створення нової версії шаблону",
    responses={
        400: {
            "model": schemas.HTTPError,
            "description": "Invalid template version structure",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Template version structure is invalid. "
                            "Reason: ..."
                        )
                    }
                }
            },
        },
        404: {
            "model": schemas.HTTPError,
            "description": "Template was not found",
            "content": {
                "application/json": {
                    "example": {"detail": ("Template was not found")}
                }
            },
        },
        409: {
            "model": schemas.HTTPError,
            "description": (
                "Conflict: template version with this uuid " "already exists"
            ),
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Conflict: template version with this version tag "
                            "already exists"
                        )
                    }
                }
            },
        },
    },
)
def create_template_version(
    template_uuid: uuid.UUID,
    docx_file: fastapi.UploadFile = fastapi.File(...),
    json_file: fastapi.UploadFile = fastapi.File(...),
    version_tag: str = fastapi.Form(...),
    message: str = fastapi.Form(...),
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):
    tpl = repo.get(template_uuid)
    if tpl is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template was not found.",
        )

    if tpl.get_version(version_tag) is not None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_409_CONFLICT,
            detail="Version already exists.",
        )
    try:
        create_data = template.schema.TemplateVersionCreate(
            tag=template.VersionTag.from_str(version_tag),
            message=message,
            docx_file=io.BytesIO(docx_file.file.read()),
            json_file=io.BytesIO(json_file.file.read()),
        )
        version = repo.create_version(tpl, create_data)
        return version
    except template.errors.TemplateValidationError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.post(
    "/upload",
    response_model=template.schema.TemplateVersionResponse,
    responses={
        400: {
            "model": schemas.HTTPError,
            "description": "Invalid template version structure",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Template version structure is invalid. "
                            "Reason: ..."
                        )
                    }
                }
            },
        },
        409: {
            "model": schemas.HTTPError,
            "description": (
                "Conflict: template version with this uuid " "already exists"
            ),
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Conflict: template version with this version tag "
                            "already exists"
                        )
                    }
                }
            },
        },
    },
    summary="Створення нової версії шаблону на основі zip файлу",
    description="""
Очікується `.zip` файл з версією шаблону. Zip має відповідати
визначеній структурі:

```
v0.0.1
├── meta.yaml     // файл з мета інформацією про версію
├── template.docx // документ шаблону
├── template.json // приклад даних
└── static        // директорія зі статикою
    └── image.jpg
```

Приклад `meta.yaml` для версії шаблону:

```yaml
tag: "v0.0.1"
message: "This version is different from previous because ..."
created_at: "2024-05-30"
updated_at: "2024-05-30"
```
""",
)
def create_template_version_from_zip(
    template_uuid: uuid.UUID,
    file: fastapi.UploadFile = fastapi.File(...),
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):
    tpl = repo.get(template_uuid)
    if tpl is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template was not found.",
        )

    zip_bytes = io.BytesIO(file.file.read())
    try:
        version = repo.create_version_from_zip_bytes(tpl, zip_bytes)
        return version

    except template.errors.TemplateValidationError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except template.errors.DuplicationError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Conflict: {e}",
        )


@router.patch(
    "/{version_tag}",
    response_model=template.schema.TemplateVersionResponse,
    summary="Редагування метаданих версії шаблону",
    responses={
        404: {
            "model": schemas.HTTPError,
            "description": "Template version was not found",
            "content": {
                "application/json": {
                    "example": {"detail": ("Template version was not found")}
                }
            },
        }
    },
)
def update_template_version_by_tag(
    template_uuid: uuid.UUID,
    version_tag: str,
    updates: template.schema.TemplateVersionUpdate,
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):

    tpl = repo.get(template_uuid)
    if tpl is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template was not found.",
        )

    version = repo.get_version(tpl, version_tag)

    if version is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template version was not found",
        )

    updated_version = repo.update_version(tpl, version, updates)
    return updated_version
