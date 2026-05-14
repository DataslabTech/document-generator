"""Модуль описує базові компоненти метаданих."""

import dataclasses
import datetime
import io
import re
from typing import Any, Self

import pydantic
import yaml

VERSION_PATTERN = r"^v\d+\.\d+\.\d+$"
PLAIN_STRING_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
FIELD_ORDER = {
    "created_at": 0,
    "description": 10,
    "id": 20,
    "labels": 30,
    "message": 40,
    "tag": 50,
    "title": 60,
    "updated_at": 70,
    "versions": 80,
}


def is_version(version: str) -> bool:
    """Перевірити, чи є рядок валідним версійним тегом.

    Валідний версійний тег має вигляд `v1.12.3` відповідно до
    [Semantic versioning](https://semver.org).

    Args:
      version: рядок версійного тегу.

    Returns:
      Булеве значення, що визначає валідність версійного тегу.
    """
    match = re.match(VERSION_PATTERN, version)
    return bool(match)


def parse_version(version: str) -> tuple[int, int, int]:
    """Розпарсити версійний тег на семантичні компоненти.

    Args:
        version: рядок версійного тегу.

    Returns:
      Семантичні компоненти відповідно до
      [Semantic versioning](https://semver.org).

    Raises:
      ValueError: Помилка в разі невалідності версійного тегу.
    """
    if not is_version(version):
        raise ValueError(f"Invalid version tag format: {version=}")

    parts = version[1:]
    splitted_str_parts = parts.split(".")
    return (
        int(splitted_str_parts[0]),
        int(splitted_str_parts[1]),
        int(splitted_str_parts[2]),
    )


@dataclasses.dataclass
class VersionTag:
    """Версійний тег з відокремленими семантичними компонентами.

    Attributes:
        `major`: Компонент major.
        `minor`: Компонент minor.
        `patch`: Компонент patch.
    """

    major: int
    minor: int
    patch: int

    @property
    def tag(self) -> str:
        """Повний версійний тег."""
        return f"v{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_str(cls, tag: str) -> "VersionTag":
        """Створити ``VersionTag` з рядка версійного тегу.

        Args:
          version: Рядок версійного тегу.

        Returns:
          Обʼєкт `VersionTag`.

        Raises:
          ValueError: Помилка в разі невалідності версійного тегу.
        """
        major, minor, patch = parse_version(tag)
        return cls(major=major, minor=minor, patch=patch)

    def is_equal_to(self, tag: "VersionTag") -> bool:
        """Перевірити рівність з іншим `VersionTag`.

        Args:
          tag: `VersionTag` для порівняння.

        Returns:
          Булеве значення. `True`, якщо теги рівні, `False` інакше.
        """
        return (
            self.major == tag.major
            and self.minor == tag.minor
            and self.patch == tag.patch
        )

    def less_than(self, tag: "VersionTag") -> bool:
        """Перевірити, чи версія нижча за версію наданого `VersionTag`.

        Args:
          tag: `VersionTag` для порівняння.

        Returns:
          Булеве значення. `True`, якщо версія нижча за надану, `False` інакше.
        """
        if self.major != tag.major:
            return self.major < tag.major

        if self.minor != tag.minor:
            return self.minor < tag.minor

        return self.patch < tag.patch


def compare_version_tags(tag1: VersionTag, tag2: VersionTag) -> int:
    """Порівняти два версійних теги.

    Визначити, який з тегів має вищу версію. Корисно використовувати
    як `key` в `sorted()`. Приклад:
    ```python
    versions: list[VersionTag] = [...]
    sorted(
        versions,
        key=functools.cmp_to_key(compare_version_tags),
        reverse=True,
    )
    ```
    Args:
      tag1: перший `VersionTag` для порівняння.
      tag2: другий `VersionTag` для порівняння.

    Returns:
      -1: tag1 < tag2
       0: tag1 == tag2
       1: tag1 > tag2

    """
    if tag1.is_equal_to(tag2):
        return 0

    return -1 if tag1.less_than(tag2) else 1


class VersionTagMixin(pydantic.BaseModel):
    """Mixin для `pydantic` моделей, що мають містити
    атрибут типу `VersionTag`.

    Клас надає правила валідації та сереалізації атрибуту `tag`.

    Attributes:
        tag: Oбʼєкт версійного тегу `VersionTag`.
    """

    tag: VersionTag = pydantic.Field(examples=["v2.3.0", "v2.0.0", "v1.15.2"])

    @pydantic.field_validator("tag", mode="before")
    @classmethod
    def _validate_tag(cls, value: Any) -> VersionTag:
        if isinstance(value, str):
            return VersionTag.from_str(value)

        if isinstance(value, VersionTag):
            return value

        raise ValueError("Invalid version type")

    @pydantic.field_serializer("tag")
    def serialize_tag(self, version: VersionTag) -> str:
        """Сереалізувати атрибут `tag`.

        Args:
          version: Обʼєкт `VersionTag`.

        Returns:
          Рядок версійного тегу відповідно до
          [Semantic versioning](https://semver.org).
        """
        return version.tag


class MetaData(pydantic.BaseModel):
    """Базові метадані.

    Attributes:
        `created_at`: Дата створення.
        `updated_at`: Дата останнього оновлення.
    """

    created_at: datetime.datetime = pydantic.Field(
        default_factory=datetime.datetime.now
    )
    updated_at: datetime.datetime | None = None

    @classmethod
    def from_bytes(cls, stream: io.BytesIO) -> Self:
        """Утворити `MetaData` з байтового потоку `.yaml`.

        Args:
          `stream`: Байтовий потік `.yaml` файлу метаданих.

        Returns:
          Обʼєкт `MetaData`.

        Raises:
          `pydantic.ValidationError`: Помилка в разі невідповідності
          байтового потоку заданій структурі.
        """

        data = stream.read()
        meta_raw = yaml.safe_load(data)
        meta = cls.model_validate(meta_raw)
        return meta

    def to_bytes(self) -> io.BytesIO:
        """Утворити байтовий потік `.yaml` файлу з обʼєкту `MetaData`.

        Returns:
          `BytesIO` потік `.yaml` файлу з даними `MetaData`.
        """
        model_dict = _order_mapping(self.model_dump(mode="json"))
        output = io.BytesIO()
        output.write(_dump_yaml(model_dict).encode("utf-8"))
        output.seek(0)
        return output


def _dump_yaml(data: dict[str, Any]) -> str:
    """Сереалізувати JSON-подібний словник в читабельний YAML."""
    lines = _to_yaml_lines(data)
    return "\n".join(lines) + "\n"


def _order_mapping(data: dict[str, Any]) -> dict[str, Any]:
    ordered_items = sorted(
        data.items(),
        key=lambda item: (FIELD_ORDER.get(item[0], 100), item[0]),
    )
    return {key: value for key, value in ordered_items}


def _to_yaml_lines(value: Any, indent: int = 0) -> list[str]:
    prefix = " " * indent

    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, list) and not item:
                lines.append(f"{prefix}{key}: []")
            elif isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.extend(_to_yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_format_scalar(item)}")
        return lines

    if isinstance(value, list):
        if not value:
            return [f"{prefix}[]"]

        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                nested_lines = _to_yaml_lines(item, indent + 2)
                lines.append(f"{prefix}- {nested_lines[0].lstrip()}")
                lines.extend(nested_lines[1:])
            else:
                lines.append(f"{prefix}- {_format_scalar(item)}")
        return lines

    return [f"{prefix}{_format_scalar(value)}"]


def _format_scalar(value: Any) -> str:
    if value is None:
        return "null"

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (int, float)):
        return str(value)

    if isinstance(value, str):
        if PLAIN_STRING_PATTERN.fullmatch(value):
            return value

        escaped_value = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped_value}"'

    raise TypeError(f"Unsupported metadata field type: {type(value)!r}")
