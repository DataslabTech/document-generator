"""Допоміжні схеми для API."""

import pydantic

from app.internal.template import payload


class HTTPError(pydantic.BaseModel):
    """DTO HTTP помилки."""

    detail: str


class HttpPayloadValidationError(pydantic.BaseModel):
    """DTO for payload validation error."""

    detail: str
    validation_result: payload.ValidationResult | str
