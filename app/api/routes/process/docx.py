"""Модуль описує роути `/process/docx`"""

import uuid
from typing import Any, Final

import fastapi
from fastapi import responses

from app.api import injection, schemas
from app.internal import docx, template

DOCX_MIME_TYPE: Final = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

router = fastapi.APIRouter()

router = fastapi.APIRouter(prefix="/docx")


@router.post(
    "/{template_uuid}",
    response_class=responses.StreamingResponse,
    tags=["docx"],
    summary="Згенерувати документ за останньою версією шаблону",
    responses={
        400: {
            "model": schemas.HTTPError,
            "description": "Cannot generate document.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": ("Cannot generate document. Reason: ...")
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
    },
)
def create_docx_for_latest_version(
    template_uuid: uuid.UUID,
    data: dict[str, Any],
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
    generator: docx.DocxGenerator = fastapi.Depends(injection.get_generator),
):
    tpl = repo.get(template_uuid)
    if tpl is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template was not found",
        )

    version = tpl.get_latest_version()
    if version is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template version was not found",
        )

    try:
        template_stream = repo.load_template_docx(tpl, version)
        generated_docx = generator.generate_bytes(template_stream, data)

        return responses.StreamingResponse(
            generated_docx, media_type=DOCX_MIME_TYPE
        )

    except docx.errors.DocumentGenerationError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{template_uuid}/{version_tag}",
    response_class=responses.StreamingResponse,
    tags=["docx"],
    summary="Згенерувати документ за обраною версією шаблону",
    responses={
        400: {
            "model": schemas.HTTPError,
            "description": "Cannot generate document.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": ("Cannot generate document. Reason: ...")
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
    },
)
def create_docx_for_version(
    template_uuid: uuid.UUID,
    version_tag: str,
    data: dict[str, Any],
    repo: template.TemplateRepository = fastapi.Depends(injection.get_repo),
    generator: docx.DocxGenerator = fastapi.Depends(injection.get_generator),
):
    tpl = repo.get(template_uuid)
    if tpl is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template was not found",
        )

    version = tpl.get_version(version_tag)
    if version is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail="Template version was not found",
        )

    try:
        template_stream = repo.load_template_docx(tpl, version)
        generated_docx = generator.generate_bytes(template_stream, data)
        return responses.StreamingResponse(
            generated_docx, media_type=DOCX_MIME_TYPE
        )
    except docx.errors.DocumentGenerationError as e:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST, detail=e
        )
