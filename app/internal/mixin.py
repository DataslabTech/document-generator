"""Модуль надає універсальні Mixins для застосунку."""

from typing import Any


class SingletonMixin:
    """Mixin для реалізації патерну Singleton."""

    _instance = None

    def __new__(cls, *args: list[Any], **kwargs: dict[str, Any]):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
