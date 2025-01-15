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
                    "detail": ("Template body is invalid."),
                    "validation_result": {
                        "missing_keys": ["KEY1, KEY2, KEY3.SUBKEY5"],
                        "extra_keys": ["LISTED_KEY[4].VALUE"],
                        "type_mismatches": [
                            "BOOL_KEY (expected bool, got int)",
                            "INT_KEY (expected int, got str)",
                            "LISTED_KEY[2] (expected dict, got str)",
                        ],
                    },
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

    validation_report = repo.validate_generation_payload(tpl, version, data)
    if not validation_report.valid:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            content=schemas.HttpPayloadValidationError(
                detail="Template body is invalid.",
                validation_result=validation_report,
            ).model_dump(mode="json"),
        )

    try:
        template_stream = repo.load_template_docx(tpl, version)
        generated_docx = generator.generate_bytes(template_stream, data)

        return responses.StreamingResponse(
            generated_docx, media_type=DOCX_MIME_TYPE
        )

    except docx.errors.DocumentGenerationError as e:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            content=schemas.HttpPayloadValidationError(
                detail="Template body is invalid.",
                validation_result=str(e),
            ).model_dump(mode="json"),
        )


@router.post(
    "/{template_uuid}/{version_tag}",
    response_class=responses.StreamingResponse,
    tags=["docx"],
    summary="Згенерувати документ за обраною версією шаблону",
    responses={
        400: {
            "model": schemas.HTTPError,
            "description": "Template body is invalid.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": ("Template body is invalid."),
                        "validation_result": {
                            "missing_keys": ["KEY1, KEY2, KEY3.SUBKEY5"],
                            "extra_keys": ["LISTED_KEY[4].VALUE"],
                            "type_mismatches": [
                                "BOOL_KEY (expected bool, got int)",
                                "INT_KEY (expected int, got str)",
                                "LISTED_KEY[2] (expected dict, got str)",
                            ],
                        },
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

    validation_report = repo.validate_generation_payload(tpl, version, data)
    if not validation_report.valid:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            content=schemas.HttpPayloadValidationError(
                detail="Template body is invalid.",
                validation_result=validation_report,
            ),
        )

    try:
        template_stream = repo.load_template_docx(tpl, version)
        generated_docx = generator.generate_bytes(template_stream, data)
        return responses.StreamingResponse(
            generated_docx, media_type=DOCX_MIME_TYPE
        )
    except docx.errors.DocumentGenerationError as e:
        return fastapi.responses.JSONResponse(
            status_code=fastapi.status.HTTP_400_BAD_REQUEST,
            content=schemas.HttpPayloadValidationError(
                detail="Template body is invalid.",
                validation_result=str(e),
            ),
        )
