"""Модуль описує роути `/templates`"""

import io
import uuid

import fastapi

from app.api import injection, schemas
from app.internal import template

router = fastapi.APIRouter()


@router.get(
    "/",
    response_model=list[template.schema.TemplateResponse],
    summary="Список шаблонів",
)
def get_templates(
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):
    return repo.list_all()


@router.get(
    "/{template_uuid}",
    response_model=template.schema.TemplateResponse,
    summary="Шаблон за UUID",
    responses={
        404: {
            "model": schemas.HTTPError,
            "description": "Template was not found",
            "content": {
                "application/json": {
                    "example": {"detail": ("Template was not found")}
                }
            },
        }
    },
)
def get_template_by_uuid(
    template_uuid: uuid.UUID,
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):
    tpl = repo.get(template_uuid)
    if tpl is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template was not found",
        )

    return tpl


@router.post(
    "/",
    response_model=template.schema.TemplateResponse,
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
    },
)
def create_template(
    create_data: template.schema.TemplateCreate,
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):
    try:
        tpl = repo.create(create_data)
    except template.errors.TemplateValidationError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=e
        )

    return tpl


@router.post(
    "/upload",
    response_model=template.schema.TemplateResponse,
    responses={
        400: {
            "model": schemas.HTTPError,
            "description": "Invalid template structure",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Template structure is invalid. Reason: ..."
                        )
                    }
                }
            },
        },
        409: {
            "model": schemas.HTTPError,
            "description": "Conflict: template with this uuid already exists",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Conflict: template with this uuid already exists"
                        )
                    }
                }
            },
        },
    },
    summary="Створення нового шаблону на основі zip файлу",
    description="""
Очікується `.zip` файл з шаблоном. Шаблон має відповідати визначеній структурі:

```
{template_uuid} // ідентифікатор шаблону
├── meta.yaml  // файл з допоміжною мета інформацією про шаблон
└── versions
    ├── v0.0.1
    │   ├── template.docx // документ шаблону
    │   ├── template.json // приклад даних
    │   └── static // директорія з зображеннями для особливих випадків
    │       └── image.jpg
    └── v0.0.2
        ├── template.docx
        ├── template.json
        └── static
            └── image.jpg
```

Приклад `meta.yaml` для шаблону:

```
id: d3a17928-e147-423e-825a-80c987f275a9 // не обовʼязкове поле
title: Report document template
description: Report document description
versions:
- v0.0.2
- v0.0.1
labels:
- example
- template
- testing
created_at: '2024-06-28T14:30:52.773130' // не обовʼязкове поле
updated_at: null // не обовʼязкове поле
```

Приклад `meta.yaml` для версії шаблону:

```
tag: v0.0.1
message: Test template
created_at: '2024-06-28T14:30:36.420872'  // не обовʼязкове поле
updated_at: null  // не обовʼязкове поле
```
""",
)
def create_template_from_zip(
    file: fastapi.UploadFile = fastapi.File(...),
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):
    if file.content_type != "application/zip":
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail="Template structure is invalid. Reason: "
            "only .zip files are allowed",
        )

    zip_bytes = io.BytesIO(file.file.read())
    try:
        tpl = repo.create_from_zip_bytes(zip_bytes)
        return tpl
    except template.errors.TemplateValidationError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Template structure is invalid. Reason: {e}",
        )
    except template.errors.DuplicationError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=f"Conflict: {e}",
        )


@router.patch(
    "/{template_uuid}",
    response_model=template.schema.TemplateResponse,
    summary="Редагування метаданих шаблону",
    responses={
        404: {
            "model": schemas.HTTPError,
            "description": "Template was not found",
            "content": {
                "application/json": {
                    "example": {"detail": ("Template was not found")}
                }
            },
        }
    },
)
def update_template(
    template_uuid: uuid.UUID,
    updates: template.schema.TemplateUpdate,
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
):
    tpl = repo.get(template_uuid)
    if tpl is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template was not found",
        )

    updated_tpl = repo.update(
        tpl, updates.title, updates.description, updates.labels
    )

    return updated_tpl
