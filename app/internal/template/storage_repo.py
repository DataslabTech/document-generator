"""Модуль описує класи `StorageTemplateRepository` та `TemplateCache`"""

import io
import json
import pathlib
import uuid
from abc import ABC, abstractmethod

from app.core import config
from app.internal import mixin, storage
from app.internal.template import entity, errors
from app.internal.template import factory as tpl_factory
from app.internal.template import repo, schema
from app.internal.template import validator as tpl_validator
from app.internal.template import version as tpl_version


class TemplateCache(ABC):
    """Кеш для доступу до шаблонів."""

    @abstractmethod
    def list(self) -> list[entity.Template]:
        """Отримати список усіх обʼєктів `Template`.

        Returns:
          Список усіх шаблонів.
        """

    @abstractmethod
    def add(self, template: entity.Template) -> None:
        """Додати шаблон до кешу.

        Args:
          template: Шаблон.
        """

    @abstractmethod
    def get(self, template_uuid: uuid.UUID) -> entity.Template | None:
        """Отримати шаблон за ідентифікатором.

        Args:
          template_uuid: Унікальний ідентифікатор шаблону.

        Returns:
          Шаблон або `None`, якщо шаблону не знайдено.
        """


class MemoryTemplateCache(TemplateCache, mixin.SingletonMixin):
    """In-memory кеш для доступу до шаблонів. Імплементація `TemplateCache`

    Реалізує шаблон `Singleton`.
    """

    def __init__(self):
        """Створює новий обʼєкт `MemoryTemplateCache`."""
        if not hasattr(self, "_initialized"):
            self._memory: dict[uuid.UUID, entity.Template] = {}
            self._initialized = True

    def list(self) -> list[entity.Template]:
        return list(self._memory.values())

    def add(self, template: entity.Template) -> None:
        self._memory[template.id] = template

    def get(self, template_uuid: uuid.UUID) -> entity.Template | None:
        return self._memory.get(template_uuid)


class StorageTemplateRepository(repo.TemplateRepository):
    """Репозиторій для операцій з `Template` на основі файлового сховища.

    Імплементація `TemplateRepository`.
    """

    def __init__(
        self,
        file_storage: storage.Storage,
        tmp_storage: storage.Storage,
        tmp_validator: tpl_validator.TemplateValidator,
        cache: TemplateCache,
        factory: tpl_factory.TemplateFactory,
    ):
        """Створює новий обʼєкт `StorageTemplateRepository`.

        Args:
          file_storage: Екземпляр сховища, де зберігаються шаблони.
          tmp_storage: Екземпляр локального сховища для тимчасових файлів.
          tmp_validator: Валідатор з tmp_storage.
          cache: Кеш для доступу до шаблонів.
          factory: Фабрика для створення нових шаблонів з file_storage.
        """
        self._file_storage = file_storage
        self._tmp_storage = tmp_storage
        self._tmp_validator = tmp_validator
        self._factory = factory

        self._cache = cache

        self._tmp_path = pathlib.Path(config.settings.LOCAL_STORAGE_TMP_PATH)
        self._templates_path = pathlib.Path(
            config.settings.LOCAL_STORAGE_TEMPLATE_PATH
        )

    def setup_cache(self) -> None:
        """Наповнити кеш шаблонами.

        Слід виконувати під час старту застосунку.
        """
        for template_path in self._file_storage.listdir(self._templates_path):
            self._setup_template(template_path)

    def list_all(self) -> list[entity.Template]:
        return self._cache.list()

    def create_from_path(self, template_path: pathlib.Path) -> entity.Template:

        template = self._factory.create_template(template_path)
        self._update_template_metadata(template)
        self._cache.add(template)
        return template

    def create(self, create_data: schema.TemplateCreate) -> entity.Template:
        template_meta = entity.TemplateMetaData(
            title=create_data.title,
            description=create_data.description,
            labels=create_data.labels,
            versions=[],
        )
        template_path = self._store(template_meta)
        return self.create_from_path(template_path)

    def create_from_zip_bytes(self, zip_bytes: io.BytesIO) -> entity.Template:
        tmp_template_path = self._tmp_storage.save_dir(
            zip_bytes, self._tmp_path
        )
        try:
            return self._create_from_zip(zip_bytes, tmp_template_path)
        except errors.TemplateValidationError as e:
            raise e
        finally:
            self._tmp_storage.delete(tmp_template_path)

    def create_from_zip_file(self, zip_path: pathlib.Path) -> entity.Template:
        tmp_template_path = self._tmp_storage.extract_zip(
            zip_path, self._tmp_path
        )
        try:
            zip_bytes = self._tmp_storage.load_file(zip_path)
            return self._create_from_zip(zip_bytes, tmp_template_path)

        except errors.TemplateValidationError as e:
            raise e
        finally:
            self._tmp_storage.delete(zip_path)
            self._tmp_storage.delete(tmp_template_path)

    def get(self, template_uuid: uuid.UUID) -> entity.Template | None:
        template = self._cache.get(template_uuid)
        return template

    def update(
        self,
        template: entity.Template,
        title: str | None = None,
        description: str | None = None,
        labels: list[str] | None = None,
    ) -> entity.Template:
        if title is not None:
            template.title = title

        if description is not None:
            template.description = description

        if labels is not None:
            template.labels = labels

        self._update_template_metadata(template)
        return template

    def add_version(
        self, template: entity.Template, version: tpl_version.TemplateVersion
    ) -> None:
        template.add_version(version)
        self._update_template_metadata(template)

    def get_version(
        self, template: entity.Template, version_tag: str
    ) -> tpl_version.TemplateVersion | None:
        version = template.get_version(version_tag)
        return version

    def get_versions(
        self, template: entity.Template
    ) -> list[tpl_version.TemplateVersion]:
        versions = template.get_versions()
        return versions

    def load_template_docx(
        self, template: entity.Template, version: tpl_version.TemplateVersion
    ) -> io.BytesIO:
        version_path = self._get_template_version_path(
            template, version.tag_str
        )
        docx_path = tpl_validator.get_template_docx_path(version_path)

        return self._file_storage.load_file(docx_path)

    def load_template_json(
        self, template: entity.Template, version: tpl_version.TemplateVersion
    ) -> io.BytesIO:
        version_path = self._get_template_version_path(
            template, version.tag_str
        )
        json_path = tpl_validator.get_template_json_path(version_path)
        json_stream = self._file_storage.load_file(json_path)

        return json.load(json_stream)

    def _store_version(
        self,
        template: entity.Template,
        version_meta: tpl_version.TemplateVersionMetaData,
        docx_bytes: io.BytesIO,
        json_bytes: io.BytesIO,
    ) -> pathlib.Path:
        version_path = self._get_template_version_path(
            template, version_meta.tag.tag
        )
        if self._file_storage.exists(version_path):
            raise errors.DuplicationError("...")

        self._file_storage.mkdir(version_path)

        meta_path = tpl_validator.get_meta_path(version_path)
        self._file_storage.save_file(meta_path, version_meta.to_bytes())

        docx_path = tpl_validator.get_template_docx_path(version_path)
        self._file_storage.save_file(docx_path, docx_bytes)

        json_path = tpl_validator.get_template_json_path(version_path)
        self._file_storage.save_file(json_path, json_bytes)

        static_path = tpl_validator.get_static_path(version_path)
        self._file_storage.mkdir(static_path)

        return version_path

    def create_version(
        self,
        template: entity.Template,
        create_data: schema.TemplateVersionCreate,
    ) -> tpl_version.TemplateVersion:
        template_version_meta = tpl_version.TemplateVersionMetaData(
            tag=create_data.tag, message=create_data.message
        )
        version_path = self._store_version(
            template,
            template_version_meta,
            create_data.docx_file,
            create_data.json_file,
        )
        return self.create_version_from_path(template, version_path)

    def create_version_from_path(
        self,
        template: entity.Template,
        version_path: pathlib.Path,
        update_template_metadata: bool = True,
        update_template: bool = True,
    ) -> tpl_version.TemplateVersion:
        version = self._factory.create_template_version(version_path)
        self._update_template_version_metadata(template, version)
        if update_template:
            template.add_version(version)
        if update_template_metadata:
            self._update_template_metadata(template)
        return version

    def create_version_from_zip_bytes(
        self,
        template: entity.Template,
        zip_bytes: io.BytesIO,
    ) -> tpl_version.TemplateVersion:
        tmp_version_path = self._tmp_storage.save_dir(
            zip_bytes, self._tmp_path
        )
        try:
            return self._create_version_from_zip(
                template, zip_bytes, tmp_version_path
            )
        except errors.TemplateValidationError as e:
            raise e
        finally:
            self._tmp_storage.delete(tmp_version_path)

    def update_version(
        self,
        template: entity.Template,
        version: tpl_version.TemplateVersion,
        updates: schema.TemplateVersionUpdate,
    ) -> tpl_version.TemplateVersion:
        if updates.message is not None:
            version.message = updates.message

        self._update_template_version_metadata(template, version)
        return version

    def _check_template_duplication(self, template_uuid: uuid.UUID) -> None:
        if self.get(template_uuid) is not None:
            raise errors.DuplicationError(
                f"Template with this uuid already exists: {template_uuid}"
            )

    def _setup_template(self, template_path: pathlib.Path) -> entity.Template:
        template = self.create_from_path(template_path)
        versions_path = tpl_validator.get_versions_path(template_path)
        for version_path in self._file_storage.listdir(versions_path):
            self.create_version_from_path(
                template,
                version_path,
                update_template_metadata=False,
                update_template=False,
            )
        return template

    def _store(self, meta: entity.TemplateMetaData) -> pathlib.Path:
        template_path = self._templates_path / str(meta.id)
        if self._file_storage.exists(template_path):
            raise errors.DuplicationError("...")

        self._file_storage.mkdir(template_path)
        self._file_storage.mkdir(
            tpl_validator.get_versions_path(template_path)
        )
        meta_path = tpl_validator.get_meta_path(template_path)
        self._file_storage.save_file(meta_path, meta.to_bytes())

        return template_path

    def _check_version_duplication(
        self, template: entity.Template, version_tag: str
    ) -> None:
        if template.get_version(version_tag) is not None:
            raise errors.DuplicationError(
                "Version with this tag already exists for "
                f"template {template.id}: {version_tag}"
            )

    def _create_from_zip(
        self, zip_bytes: io.BytesIO, tmp_template_path: pathlib.Path
    ) -> entity.Template:
        meta = self._tmp_validator.validate_template_dir(tmp_template_path)
        self._check_template_duplication(meta.id)

        template_path = self._templates_path / str(meta.id)
        self._file_storage.save_dir(zip_bytes, self._templates_path)

        return self.create_from_path(template_path)

    def _get_template_path(self, template: entity.Template) -> pathlib.Path:
        return self._templates_path / str(template.id)

    def _get_template_version_path(
        self, template: entity.Template, version_tag: str
    ) -> pathlib.Path:
        template_path = self._get_template_path(template)
        return tpl_validator.get_versions_path(template_path) / version_tag

    def _update_template_metadata(self, template: entity.Template):
        meta_bytes = template.get_meta_bytes()
        template_path = self._get_template_path(template)
        meta_path = tpl_validator.get_meta_path(template_path)
        self._file_storage.save_file(meta_path, meta_bytes)

    def _update_template_version_metadata(
        self, template: entity.Template, version: tpl_version.TemplateVersion
    ):
        meta_bytes = version.get_meta_bytes()
        version_path = self._get_template_version_path(
            template, version.tag_str
        )
        meta_path = tpl_validator.get_meta_path(version_path)
        self._file_storage.save_file(meta_path, meta_bytes)

    def _create_version_from_zip(
        self,
        template: entity.Template,
        zip_bytes: io.BytesIO,
        tmp_version_path: pathlib.Path,
    ) -> tpl_version.TemplateVersion:
        meta = self._tmp_validator.validate_version_dir(tmp_version_path)
        self._check_version_duplication(template, meta.tag.tag)

        template_path = self._get_template_path(template)
        version_path = tpl_validator.get_versions_path(template_path)

        self._file_storage.save_dir(zip_bytes, version_path)
        return self.create_version_from_path(
            template, version_path / meta.tag.tag
        )
