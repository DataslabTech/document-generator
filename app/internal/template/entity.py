"""
Модуль описує клас `Template` та клас метаданих `TemplateMetaData`
"""

import datetime
import functools
import io
import uuid
from typing import Annotated, Any

import pydantic

from app.internal.template import meta, version


class VersionsListMixin(pydantic.BaseModel):
    """Mixin для `pydantic моделей`, що мають містити
    список версій `VersionTag`.

    Клас надає правила валідації та сереалізації такого списку.

    Attributes:
        versions: список версій `VersionTag`
    """

    versions: Annotated[
        list[meta.VersionTag],
        pydantic.Field(examples=[["v2.3.0", "v2.0.0", "v1.15.2"]]),
    ]

    @pydantic.field_validator("versions", mode="before")
    @classmethod
    def validate_versions(cls, value: Any) -> list[meta.VersionTag]:
        """Провалідувати вхідне значення для `versions`.

        Якщо вхідний тип - `list[str]`, створити з нього `list[VersionTag]`.

        Args:
          value: вхідне значення для `versions`.

        Returns:
          Сортований в спадному порядку писок версій `list[VersionTag]`.

        Raises:
          ValueError: Рядок версії не відповідає визначеному формату.
          pydantic.ValidationError: Помилка при валідації моделі Pydantic.
        """
        versions: list[meta.VersionTag] = []
        for ver in value:
            if isinstance(ver, str):
                versions.append(meta.VersionTag.from_str(ver))
            elif isinstance(ver, meta.VersionTag):
                versions.append(ver)
        return sorted(
            versions,
            key=functools.cmp_to_key(meta.compare_version_tags),
            reverse=True,
        )

    @pydantic.field_serializer("versions")
    def serialize_versions(self, versions: list[meta.VersionTag]) -> list[str]:
        """Сереалізувати значення `versions`.

        Перетворити `versions` в масив `list[str]` вигляду:

        `["v1.0.0", "v0.5.2", "0.0.3"]`.

        Args:
          versions: список `versions`.

        Returns:
          Список версій в типі `list[str]`.
        """
        return [
            version.tag
            for version in sorted(
                versions,
                key=functools.cmp_to_key(meta.compare_version_tags),
                reverse=True,
            )
        ]

    def add_version(self, version_tag: meta.VersionTag) -> None:
        """Додати нову версію до `versions`.

        Args:
          version: версія для додавання в список.
        """
        index = self._find_insert_posititon(
            0, len(self.versions) - 1, version_tag
        )
        self.versions.insert(index, version_tag)

    def _find_insert_posititon(
        self, low: int, high: int, version_tag: meta.VersionTag
    ) -> int:
        while low <= high:
            mid = (low + high) // 2

            if self.versions[mid].less_than(version_tag):
                high = mid - 1
            else:
                low = mid + 1

        return low


class TemplateMetaData(meta.MetaData, VersionsListMixin):
    """Метадані шаблону

    Attributes:
        `id`: унікальний UUID шаблону
        `title`: назва шаблону
        `description`: опис шаблону
        `labels`: перелік міток шаблону
        `versions`: список доступних версій шаблону
        `created_at`: дата створення
        `updated_at`: дата останнього оновлення
    """

    id: pydantic.UUID4 = pydantic.Field(default_factory=uuid.uuid4)
    title: str
    description: str
    labels: list[str]

    @classmethod
    def from_bytes(cls, stream: io.BytesIO) -> "TemplateMetaData":
        """
        Утворити `TemplateMetaData` з байтового потоку.

        Байтовий потік має представляти `.yaml` файл наступного вигляду:

        ```yaml
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
        updated_at: null                         // не обовʼязкове поле
        ```

        Args:
          `stream`: Байтовий потік `.yaml` файлу метаданих.

        Returns:
          Обʼєкт `TemplateMetaData`.

        Raises:
          `pydantic.ValidationError`: Помилка в разі невідповідності
          байтового потоку заданій структурі.
        """
        return super(TemplateMetaData, cls).from_bytes(stream)


class Template:
    """Інформація про шаблон. Агрегує версії шаблону.

    Attributes:
        `id`: Унікальний UUID шаблону.
        `title`: Назва шаблону.
        `description`: Опис шаблону.
        `labels`: Перелік міток шаблону.
        `versions`: Список доступних версій шаблону.
        `created_at`: Дата створення.
        `updated_at`: Дата останнього оновлення.
    """

    def __init__(self, meta_data: TemplateMetaData):
        """Утворити новий обʼєкт `Template`.

        Args:
          meta_data: Метадані шаблону.
        """
        self._meta = meta_data
        self._versions: dict["str", "version.TemplateVersion"] = {}

    @property
    def title(self) -> str:
        """Назва шаблону"""
        return self._meta.title

    @title.setter
    def title(self, title: str) -> None:
        self._meta.title = title

    @property
    def id(self) -> pydantic.UUID4:
        """Унікальний UUID шаблону."""
        return self._meta.id

    @property
    def description(self) -> str:
        """Опис шаблону."""
        return self._meta.description

    @description.setter
    def description(self, description: str) -> None:
        self._meta.description = description

    @property
    def versions(self) -> list[meta.VersionTag]:
        """Список доступних версій шаблону."""
        return self._meta.versions

    @property
    def labels(self) -> list[str]:
        """Перелік міток шаблону."""
        return self._meta.labels

    @labels.setter
    def labels(self, labels: list[str]) -> None:
        self._meta.labels = labels

    @property
    def created_at(self) -> datetime.datetime:
        """Дата створення."""
        return self._meta.created_at

    @property
    def updated_at(self) -> datetime.datetime | None:
        """Дата останнього оновлення."""
        return self._meta.updated_at

    @updated_at.setter
    def updated_at(self, value: datetime.datetime) -> None:
        self._meta.updated_at = value

    def get_version(self, version_tag: str) -> version.TemplateVersion | None:
        """Отримати версію шаблона за версійним тегом.

        Args:
          version_tag: Версійний тег шаблону.

        Returns:
          Версія шаблону `TemplateVersion` або `None`,
          якщо версії за тегом не знайдено.

        Raises:
          ValueError: Помилка в разі невалідності версійного тегу.
        """

        if not meta.is_version(version_tag):
            raise ValueError(f"Invalid version tag format: {version_tag=}")

        return self._versions.get(version_tag)

    def get_latest_version(self) -> version.TemplateVersion | None:
        """Отримати останню версію шаблону.

        Returns:
          Версія шаблону `TemplateVersion` або `None`,
          якщо версій немає.
        """
        if len(self._meta.versions) == 0:
            return None
        latest_tag = self._meta.versions[0]
        return self.get_version(latest_tag.tag)

    def get_versions(self) -> list[version.TemplateVersion]:
        """Отримати список усіх версій шаблону.

        Returns:
          Список `list[TemplateVersion]` версій шаблону.
        """
        return [
            self._versions[v.tag]
            for v in self._meta.versions
            if v.tag in self._versions
        ]

    def add_version(
        self, version_obj: version.TemplateVersion, update_meta: bool = True
    ) -> None:
        """Додати версію до шаблону.

        Args:
          version_obj: Версія шаблону.
          update_meta: Чи потрібно оновлювати метадані.
        """
        added_version = self.get_version(version_obj.tag.tag)
        if added_version is not None:
            raise ValueError(f"Version already exists: {version_obj.tag.tag}")

        if update_meta:
            self._meta.add_version(version_obj.tag)

        self._versions[version_obj.tag.tag] = version_obj

    def get_meta_bytes(self) -> io.BytesIO:
        """Утворити байтовий потік `.yaml` файлу метаданих шаблону.

        Returns:
          `BytesIO` потік `.yaml` файлу з даними `TemplateMetaData`.
        """
        return self._meta.to_bytes()
