"""
Модуль надає функції для отримання шляхів до компонентів шаблону інтерфейс
TemplateValidator та імплементацію StorageTemplateValidator
"""

import pathlib
from abc import ABC, abstractmethod

import pydantic

from app.internal import storage
from app.internal.template import entity, errors
from app.internal.template import meta as tpl_meta
from app.internal.template import version

TEMPLATE_DOCX_FILE = "template.docx"
TEMPLATE_JSON_FILE = "template.json"
META_FILE = "meta.yaml"

VERSIONS_DIR = "versions"
STATIC_DIR = "static"


def get_template_docx_path(version_path: pathlib.Path) -> pathlib.Path:
    """Отримати шлях до `template.docx` файлу з директорії версії шаблону.

    Args:
        version_path: Шлях до версії шаблону.

    Returns:
        Шлях до `template.docx` файлу шаблону.
    """
    return version_path / TEMPLATE_DOCX_FILE


def get_template_json_path(version_path: pathlib.Path) -> pathlib.Path:
    """Отримати шлях до `template.json` файлу з директорії версії шаблону.

    Args:
        version_path: Шлях до версії шаблону.

    Returns:
        Шлях до `template.json` файлу шаблону.
    """
    return version_path / TEMPLATE_JSON_FILE


def get_meta_path(root_path: pathlib.Path) -> pathlib.Path:
    """Отримати шлях до файлу метаданих з директорії шаблону або
    версії шаблону.

    Args:
        root_path: Шлях до шаблону або версії шаблону.

    Returns:
        Шлях до файлу метаданих.
    """
    return root_path / META_FILE


def get_versions_path(template_path: pathlib.Path) -> pathlib.Path:
    """Отримати шлях до директорії версій з директорії шаблону.

    Args:
        template_path: Шлях до версії шаблону.

    Returns:
        Шлях до директорії версій шаблону.
    """
    return template_path / VERSIONS_DIR


def get_static_path(version_path: pathlib.Path) -> pathlib.Path:
    """Отримати шлях до директорії статичних файлів з директорії
    версії шаблону.

    Args:
        version_path: Шлях до версії шаблону.

    Returns:
        Шлях до директорії статичних файлів.
    """
    return version_path / STATIC_DIR


class TemplateValidator(ABC):
    """
    Валідатор директорії шаблону документу та версій шаблону.
    """

    @abstractmethod
    def validate_template_dir(
        self, path: pathlib.Path
    ) -> entity.TemplateMetaData:
        """
        Перевірити директорію шаблону на коректність.

        Визначає, чи відповідає директорія наступному вигляду:

        ```
        {template_uuid} // ідентифікатор шаблону
        ├── meta.yaml   // файл з мета інформацією про шаблон
        └── versions
            ├── v0.0.1
            │   ├── meta.yaml     // файл з мета інформацією про версію
            │   ├── template.docx // документ шаблону
            │   ├── template.json // приклад даних
            │   └── static        // директорія зі статикою
            │       └── image.jpg
            └── v0.0.2
                ├── meta.yaml
                ├── template.docx
                ├── template.json
                └── static
                    └── image.jpg
        ```

        Args:
            `path` - Шлях до директорії шаблону.

        Returns:
            Обʼєкт метаданих шаблону.

        Raises:
            `TemplateValidationError`: Помилка в разі невідповідності шаблону
            визначеній структурі.
        """

    @abstractmethod
    def validate_version_dir(
        self, version_path: pathlib.Path
    ) -> version.TemplateVersionMetaData:
        """
        Перевірити директорію версії шаблону на коректність.

        Визначає, чи відповідає директорія наступному вигляду:

        ```
        v0.0.1
        ├── meta.yaml     // файл з мета інформацією про версію
        ├── template.docx // документ шаблону
        ├── template.json // приклад даних
        └── static        // директорія зі статикою
            └── image.jpg
        ```

        Args:
            `path: Pathlib.Path` - Шлях до директорії версії шаблону.

        Returns:
            Обʼєкт `TemplateVersionMetaData`.

        Raises:
            `TemplateValidationError`: Помилка в разі невідповідності
            версії шаблону визначеній структурі.
        """


class StorageTemplateValidator(TemplateValidator):
    """
    Валідатор директорії шаблону документу та версій шаблону.

    Імплементує `TemplateValidator`
    """

    def __init__(self, validator_storage: storage.Storage):
        """Створити обʼєкт валідатора.

        Args:
            `storage: storage.Storage`: обʼєкт реалізації сховища шаблонів.
        """
        self._storage = validator_storage

    def validate_template_dir(
        self, path: pathlib.Path
    ) -> entity.TemplateMetaData:

        if not self._storage.is_dir(path):
            raise errors.TemplateValidationError(
                f"Template directory not found: {path}"
            )

        meta_yaml_path = get_meta_path(path)
        meta = self._validate_meta_yaml(meta_yaml_path)

        versions_path = get_versions_path(path)
        self._validate_versions(versions_path)
        self._validate_versions_coherence(path, meta.versions)
        return meta

    def validate_version_dir(
        self, version_path: pathlib.Path
    ) -> version.TemplateVersionMetaData:

        version_name = version_path.name
        if not tpl_meta.is_version(version_name):
            raise errors.TemplateValidationError(
                "Version directory name is not a valid version: "
                f"{version_name}"
            )
        meta_yaml_path = get_meta_path(version_path)
        meta = self._validate_version_meta_yaml(meta_yaml_path)

        docx_path = get_template_docx_path(version_path)
        if not self._storage.is_file(docx_path):
            raise errors.TemplateValidationError("template.docx not found")

        json_path = get_template_json_path(version_path)
        if not self._storage.is_file(json_path):
            raise errors.TemplateValidationError("template.json not found")

        return meta

    def _validate_meta_yaml(
        self, yaml_path: pathlib.Path
    ) -> entity.TemplateMetaData:
        if not self._storage.is_file(yaml_path):
            raise errors.TemplateValidationError(
                f"meta.yaml not found: {yaml_path}"
            )

        meta_bytes = self._storage.load_file(yaml_path)
        try:
            meta = entity.TemplateMetaData.from_bytes(meta_bytes)
            return meta
        except pydantic.ValidationError as e:
            raise errors.TemplateValidationError(
                f"meta.yaml for template is not valid: {e}"
            ) from e

    def _validate_version_meta_yaml(
        self, yaml_path: pathlib.Path
    ) -> version.TemplateVersionMetaData:
        if not self._storage.is_file(yaml_path):
            raise errors.TemplateValidationError("meta.yaml not found")

        meta_bytes = self._storage.load_file(yaml_path)
        try:
            meta = version.TemplateVersionMetaData.from_bytes(meta_bytes)
        except pydantic.ValidationError as e:
            raise errors.TemplateValidationError(
                f"meta.yaml for template version is not valid: {e}"
            ) from e

        version_tag = yaml_path.parent.name
        meta_tag = meta.tag
        if version_tag != meta_tag.tag:
            raise errors.TemplateValidationError(
                "Template version tag in directory and in meta.yaml "
                "do not match"
            )

        return meta

    def _validate_versions(self, versions_dir: pathlib.Path):
        if not self._storage.is_dir(versions_dir):
            raise errors.TemplateValidationError("Versions directory not found")

        for version_path in self._storage.listdir(versions_dir):
            self.validate_version_dir(version_path)

    def _validate_versions_coherence(
        self, root: pathlib.Path, meta_versions: list[tpl_meta.VersionTag]
    ):
        versions_in_meta = {v.tag for v in meta_versions}
        versions_in_dir = {
            v.name for v in self._storage.listdir(get_versions_path(root))
        }
        equal = versions_in_meta == versions_in_dir

        if not equal:
            raise errors.TemplateValidationError(
                "Versions in meta.yaml and in versions directory do not match"
            )
