"""Модуль описує клас `TemplateVersion` та
клас метаданих `TemplateVersionMetaData`"""

import datetime
import io

from app.internal.template import meta


class TemplateVersionMetaData(meta.MetaData, meta.VersionTagMixin):
    """
    Метадані для версії шаблону.

    Attributes:
        `tag`: версійний тег
        `message`: коментар до версії
        `created_at`: дата створення
        `updated_at`: дата оновлення
    """

    message: str

    @classmethod
    def from_bytes(cls, stream: io.BytesIO) -> "TemplateVersionMetaData":
        """
        Конструктор, що утворює `MetaData` з байтового потоку.

        Байтовий потік має представляти `.yaml` файл наступного вигляду:

        ```yaml
        tag: "v0.0.1"
        message: "This version is different  from previous because ..."
        created_at: "2024-05-30"
        updated_at: "2024-05-30"
        ```

        Args:
            `stream`: Байтовий потік `.yaml` файлу метаданих.

        Returns:
            Обʼєкт `TemplateVersionMetaData`.

        Raises:
            `pydantic.ValidationError`: Помилка в разі невідповідності
            байтового потоку заданій структурі.
        """
        return super(TemplateVersionMetaData, cls).from_bytes(stream)


class TemplateVersion:
    """Інформація про версію шаблону.

    Attributes:
        `tag`: Версійний тег.
        `tag_str`: Версійний тег в рядковому представленні.
        `created_at`: Дата створення.
        `updated_at`: Дата останнього оновлення.
    """

    def __init__(self, meda_data: TemplateVersionMetaData):
        """Утворити новий обʼєкт `TemplateVersion`.

        Args:
          meta_data: Метадані версії шаблону.
        """
        self._meta = meda_data

    @property
    def tag(self) -> meta.VersionTag:
        """Версійний тег шаблону."""
        return self._meta.tag

    @property
    def tag_str(self) -> str:
        """Версійний тег в рядковому представленні."""
        return self.tag.tag

    @property
    def message(self) -> str:
        """Коментар версії шаблону."""
        return self._meta.message

    @message.setter
    def message(self, message: str) -> None:
        self._meta.message = message

    @property
    def created_at(self) -> datetime.datetime | None:
        """Дата створення."""
        return self._meta.created_at

    @property
    def updated_at(self) -> datetime.datetime | None:
        """Дата останнього оновлення."""
        return self._meta.updated_at

    @updated_at.setter
    def updated_at(self, value: datetime.datetime) -> None:
        self._meta.updated_at = value

    def get_meta_bytes(self) -> io.BytesIO:
        """Утворити байтовий потік `.yaml` файлу метаданих шаблону..

        Returns:
          `BytesIO` потік `.yaml` файлу з даними `TemplateVersionMetaData`.
        """
        return self._meta.to_bytes()
