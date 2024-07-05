"""Модуль описує інтерфейс TemplateFactory
та імплементацію StorageTemplateFactory."""

import pathlib
from abc import ABC, abstractmethod

from app.internal import storage
from app.internal.template import entity, validator, version


class TemplateFactory(ABC):
    """Фабрика шаблонів та версій шаблонів."""

    @abstractmethod
    def create_template_meta(
        self, template_path: pathlib.Path
    ) -> entity.TemplateMetaData:
        """Створити метадані шаблону за шляхом шаблону.

        Args:
          template_path: шлях до директорії шаблону.

        Returns:
          Обʼєкт метаданих шаблону.

        Raises:
          pydantic.ValidationError: Помилка при валідації моделі метаданих.
        """

    @abstractmethod
    def create_template_version_meta(
        self, version_path: pathlib.Path
    ) -> version.TemplateVersionMetaData:
        """Створити метадані версії шаблону за шляхом версії шаблону.

        Args:
          version_path: шлях до директорії версії шаблону.

        Returns:
          Обʼєкт метаданих версії шаблону.

        Raises:
          pydantic.ValidationError: Помилка при валідації моделі метаданих.
        """

    @abstractmethod
    def create_template(self, template_path: pathlib.Path) -> entity.Template:
        """Створити обʼєкт шаблону за шляхом шаблону.

        Args:
          template_path: шлях до директорії шаблону.

        Returns:
          Обʼєкт шаблону.

        Raises:
          TemplateValidatorError: Помилка при валідації директорії шаблону.
          pydantic.ValidationError: Помилка при валідації моделі метаданих.
        """

    @abstractmethod
    def create_template_version(
        self, version_path: pathlib.Path
    ) -> version.TemplateVersion:
        """Створити обʼєкт версії шаблону за шляхом версії шаблону.

        Args:
          version_path: шлях до директорії версії шаблону.

        Returns:
          Обʼєкт версії шаблону.

        Raises:
          TemplateValidatorError: Помилка при валідації директорії версії
          шаблону.
          pydantic.ValidationError: Помилка при валідації моделі метаданих.
        """


class StorageTemplateFactory(TemplateFactory):
    """Фабрика шаблонів та версій шаблонів."""

    def __init__(
        self,
        template_storage: storage.Storage,
        template_validator: validator.TemplateValidator,
    ):
        self._storage = template_storage
        self.validator = template_validator

    def create_template_meta(
        self, template_path: pathlib.Path
    ) -> entity.TemplateMetaData:
        meta_path = validator.get_meta_path(template_path)
        meta_bytes = self._storage.load_file(meta_path)
        return entity.TemplateMetaData.from_bytes(meta_bytes)

    def create_template_version_meta(
        self, version_path: pathlib.Path
    ) -> version.TemplateVersionMetaData:
        meta_path = validator.get_meta_path(version_path)
        meta_bytes = self._storage.load_file(meta_path)
        return version.TemplateVersionMetaData.from_bytes(meta_bytes)

    def create_template(self, template_path: pathlib.Path) -> entity.Template:
        self.validator.validate_template_dir(template_path)
        meta = self.create_template_meta(template_path)
        template = entity.Template(meta)

        versions_path = validator.get_versions_path(template_path)

        for version_path in self._storage.listdir(versions_path):
            template_version = self.create_template_version(version_path)
            template.add_version(template_version, update_meta=False)

        return template

    def create_template_version(
        self, version_path: pathlib.Path
    ) -> version.TemplateVersion:
        self.validator.validate_version_dir(version_path)
        meta = self.create_template_version_meta(version_path)
        template_version = version.TemplateVersion(meta)
        return template_version
