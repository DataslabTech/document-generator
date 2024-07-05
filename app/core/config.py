"""Конфігурація застосунку."""

from typing import Annotated, Any

import pydantic
import pydantic_settings


def _parse_cors(v: Any) -> list[str] | str | None:
    if v == "":
        return None
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    if isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(pydantic_settings.BaseSettings):
    """Конфігурація застосунку.

    Має бути наявний `.env` файл за шляхом app/.env

    Attributes:
        API_PREFIX: Префікс API.
        BACKEND_CORS_ORIGINS: Перелік дозволених CORS джерел.
        LOCAL_STORAGE_TEMPLATE_PATH: Шлях до директорії шаблонів.
        LOCAL_STORAGE_TMP_PATH: Шлях до директорії тимчасових файлів.
    """

    model_config = pydantic_settings.SettingsConfigDict(
        env_file="app/.env", env_ignore_empty=True, extra="ignore"
    )
    API_PREFIX: str = "/api/v1"

    BACKEND_CORS_ORIGINS: Annotated[
        list[pydantic.AnyUrl] | str | None,
        pydantic.BeforeValidator(_parse_cors),
    ] = []

    STORAGE_TYPE: str = "LOCAL"
    LOCAL_STORAGE_TEMPLATE_PATH: str = "templates"
    LOCAL_STORAGE_TMP_PATH: str = "tmp"


settings = Settings()  # type: ignore
