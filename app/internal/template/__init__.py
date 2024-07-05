"""Пакет template містить обʼєкти, що повʼязані
з шаблонами `.docx` документів."""

from app.internal.template import errors, schema
from app.internal.template.factory import (
    StorageTemplateFactory,
    TemplateFactory,
)
from app.internal.template.meta import VersionTag
from app.internal.template.repo import TemplateRepository
from app.internal.template.storage_repo import (
    MemoryTemplateCache,
    StorageTemplateRepository,
    TemplateCache,
)
from app.internal.template.validator import (
    StorageTemplateValidator,
    TemplateValidator,
)
from app.internal.template.version import TemplateVersion

__all__ = [
    "schema",
    "errors",
    "TemplateRepository",
    "TemplateCache",
    "TemplateValidator",
    "StorageTemplateValidator",
    "TemplateFactory",
    "StorageTemplateFactory",
    "StorageTemplateRepository",
    "TemplateVersion",
    "MemoryTemplateCache",
    "VersionTag",
]
