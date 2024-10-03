"""Модуль описує інтерфейс `TemplateRepository`."""

import io
import pathlib
import uuid
from abc import ABC, abstractmethod
from typing import Any

from app.internal.template import entity, payload, schema
from app.internal.template import version as tpl_version


class TemplateRepository(ABC):
    """Репозиторій для операцій з `Template`"""

    @abstractmethod
    def list_all(self) -> list[entity.Template]:
        """Отримати список усіх обʼєктів `Template`.

        Returns:
          Список усіх шаблонів.
        """

    @abstractmethod
    def create(self, create_data: schema.TemplateCreate) -> entity.Template:
        """Створити `Template` на основі вхідних даних для створення.

        Утворює нову сутність `Template` в сховищі та повертає обʼєкт.

        Args:
          create_data: DTO для створення шаблону.

        Returns:
          Новий шаблон.
        """

    @abstractmethod
    def create_from_path(self, template_path: pathlib.Path) -> entity.Template:
        """Створити `Template` на основі шляху до директорії шаблону.

        Утворює нову сутність `Template` в сховищі та повертає обʼєкт.

        Args:
          template_path: Шлях до директорії шаблону.

        Returns:
          Новий шаблон.

        Raises:
          `TemplateValidationError`: Помилка в разі невідповідності шаблону
          визначеній структурі.
        """

    @abstractmethod
    def create_from_zip_bytes(self, zip_bytes: io.BytesIO) -> entity.Template:
        """Створити `Template` на основі байтового потоку `.zip` директорії
        шаблону.

        Утворює нову сутність `Template` в сховищі та повертає обʼєкт.

        Args:
          zip_bytes: Байтовий потік `.zip директорії шаблону.

        Returns:
          Новий шаблон.

        Raises:
          `TemplateValidationError`: Помилка в разі невідповідності шаблону
          визначеній структурі.
        """

    @abstractmethod
    def get(self, template_uuid: uuid.UUID) -> entity.Template | None:
        """Отримати шаблон за ідентифікатором.

        Args:
          template_uuid: Унікальний ідентифікатор шаблону.

        Returns:
          Шаблон або `None`, якщо шаблону не знайдено.
        """

    @abstractmethod
    def update(
        self,
        template: entity.Template,
        title: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
    ) -> entity.Template:
        """
        Оновити метадані шаблону.

        Замінює значення на передане, якщо воно не `None`.

        Args:
          template: Шаблон для оновлення.
          title: Назва шаблону.
          description: Опис шаблону.
          labels: Перелік міток шаблону.

        Returns:
          Оновлений шаблон.
        """

    @abstractmethod
    def add_version(
        self, template: entity.Template, version: tpl_version.TemplateVersion
    ) -> None:
        """Додати нову версію до шаблону.

        Args:
          template: Шаблон.
          version: Версія шаблону, що треба додати.
        """

    @abstractmethod
    def get_versions(
        self, template: entity.Template
    ) -> list[tpl_version.TemplateVersion]:
        """Отримати всі версії шаблону.

        Args:
          template: Шаблон.

        Returns:
          Сортований список версій шаблону.
        """

    @abstractmethod
    def get_version(
        self, template: entity.Template, version_tag: str
    ) -> tpl_version.TemplateVersion | None:
        """Отримати версію шаблону за тегом.

        Args:
          template: Шаблон.
          version_tag: Версійний тег.

        Returns:
          Версія шаблону або `None`, якщо версії не знайдено.

        Raises:
          ValueError: Помилка в разі невалідності версійного тегу.
        """

    @abstractmethod
    def create_version(
        self,
        template: entity.Template,
        create_data: schema.TemplateVersionCreate,
    ) -> tpl_version.TemplateVersion:
        """Створити нову версію для шаблону на основі
        вхідних даних для створення.

        Args:
          template: Шаблон.
          create_data: DTO для створення версії шаблону.

        Returns:
          Створена версія шаблону.
        """

    @abstractmethod
    def create_version_from_path(
        self,
        template: entity.Template,
        version_path: pathlib.Path,
        update_template_metadata: bool = True,
        update_template: bool = True,
    ) -> tpl_version.TemplateVersion:
        """Створити нову версію для шаблону на основі шляху
        до директорії версії шаблону.

        Args:
          template: Шаблон.
          create_data: DTO для створення версії шаблону.
          version_path: Шлях до директорії версії шаблону.
          update_template_metadata: Чи треба оновлювати метадані шаблону.
          update_template: Чи треба додавати версію шаблону до обʼєкта шаблону.

        Returns:
          Створена версія шаблону.
        """

    @abstractmethod
    def create_version_from_zip_bytes(
        self,
        template: entity.Template,
        zip_bytes: io.BytesIO,
    ) -> tpl_version.TemplateVersion:
        """Створити нову версію для шаблону на основі шляху
        до директорії версії шаблону.

        Args:
          template: Шаблон.
          create_data: DTO для створення версії шаблону.
          version_path: Шлях до директорії версії шаблону.
          update_template_metadata: Чи треба оновлювати метадані шаблону.
          update_template: Чи треба додавати версію шаблону до обʼєкта шаблону.

        Returns:
          Створена версія шаблону.
        """

    @abstractmethod
    def update_version(
        self,
        template: entity.Template,
        version: tpl_version.TemplateVersion,
        updates: schema.TemplateVersionUpdate,
    ) -> tpl_version.TemplateVersion:
        """Оновити метадані версії шаблону.

        Args:
          template: Шаблон.
          version: Версія шаблону.
          updates: DTO з оновленнями метаданих.

        Returns:
          Оновлений шаблон.
        """

    @abstractmethod
    def load_template_docx(
        self, template: entity.Template, version: tpl_version.TemplateVersion
    ) -> io.BytesIO:
        """Завантажити `.docx` файл шаблону.

        Args:
          template: Шаблон.
          version: Версія шаблону.

        Returns:
          Байтовий потік `.docx` файлу.
        """

    @abstractmethod
    def load_template_json(
        self, template: entity.Template, version: tpl_version.TemplateVersion
    ) -> io.BytesIO:
        """Завантажити `.json` приклад генерації документу.

        Args:
          template: Шаблон.
          version: Версія шаблону.

        Returns:
          Байтовий потік `.json` файлу.
        """

    @abstractmethod
    def load_template_json_as_dict(
        self, template: entity.Template, version: tpl_version.TemplateVersion
    ) -> dict[str, Any]:
        """Завантажити `.json` приклад генерації документу як `dict`.

        Args:
          template: Шаблон.
          version: Версія шаблону.

        Returns:
          `dict` обʼєкт `.json` файлу.
        """

    def validate_generation_payload(
        self,
        template: entity.Template,
        version: tpl_version.TemplateVersion,
        incoming_payload: dict[str, Any],
    ) -> payload.ValidationResult:
        """Validates an incoming dictionary against a template payload structure.

        Args:
            template (Template): Template object.
            version (TemplateVersion): Specific version of the template.
            incoming_payload (dict[str, Any]): The dictionary to be validated.

        Returns:
            ValidationResult: A report on the validation, detailing any discrepancies.
        """
        payload_schema = self.load_template_json_as_dict(template, version)
        return payload.validate(payload_schema, incoming_payload)
