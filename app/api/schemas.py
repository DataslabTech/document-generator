"""Допоміжні схеми для API."""

import pydantic


class HTTPError(pydantic.BaseModel):
    """DTO HTTP помилки."""

    detail: str
