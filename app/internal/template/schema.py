"""Модуль описує DTO обʼєктів `Template` та `TemplateVersion`."""

import datetime
import io

import pydantic

from app.internal.template import entity, meta


class _TemplateBase(pydantic.BaseModel):
    title: str = pydantic.Field(examples=["Report document template"])
    description: str = pydantic.Field(
        examples=["Template for generating report documents."]
    )
    labels: list[str] = pydantic.Field(examples=[["finance", "gov", "test"]])


class TemplateCreate(_TemplateBase):
    """DTO для створення шаблону.

    Attributes:
        title: Назва шаблону.
        description: Опис шаблону.
        labels: Мітки шаблону.
    """


class TemplateUpdate(pydantic.BaseModel):
    """DTO для оновлення метаданих шаблону.

    Attributes:
        title: Назва шаблону.
        description: Опис шаблону.
        labels: Мітки шаблону.
    """

    title: str | None = pydantic.Field(
        None, examples=["Report document template"]
    )
    description: str | None = pydantic.Field(
        None, examples=["Template for generating report documents."]
    )
    labels: list[str] | None = pydantic.Field(
        None, examples=[["finance", "gov", "test"]]
    )


class TemplateResponse(_TemplateBase, entity.VersionsListMixin):
    """DTO шаблону для відповіді API.

    Attributes:
        id: Унікальний ідентифікатор.
        title: Назва шаблону.
        description: Опис шаблону.
        versions: Перелік версій шаблону.
        labels: Мітки шаблону.
        created_at: Дата створення.
        updated_at: Дата останнього оновлення.
    """

    id: pydantic.UUID4 = pydantic.Field(
        examples=["af719903-e75b-4627-a782-36ec45636013"]
    )
    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None

    class Config:
        """Конфігурація DTO."""

        from_attributes = True

    @pydantic.model_serializer()
    def serialize(self):
        """Сереалізувати DTO `TemplateResponse`.

        Задає коректний порядок полів під час сереалізації.

        Returns:
          dict з сереалізованими атрибутами обʼєкту.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "versions": self.serialize_versions(self.versions),
            "labels": self.labels,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class _TemplateVersionBase(pydantic.BaseModel):
    message: str = pydantic.Field(examples=["Changed main table layout"])


class TemplateVersionCreate(_TemplateVersionBase, meta.VersionTagMixin):
    """DTO для створення версії шаблону.

    Attributes:
        version: Версійний тег шаблону.
        message: Коментар версії.
        docx_file: Байтовий потік `.docx` файлу.
        json_file: Байтовий потік `.json` файлу.
    """

    docx_file: io.BytesIO
    json_file: io.BytesIO

    class Config:
        """Конфігурація DTO."""

        arbitrary_types_allowed = True


class TemplateVersionUpdate(pydantic.BaseModel):
    """DTO для оновлення метаданих шаблону.

    Attributes:
        message: Коментар версії.
    """

    message: str | None = None


class TemplateVersionResponse(_TemplateVersionBase, meta.VersionTagMixin):

    created_at: datetime.datetime
    updated_at: datetime.datetime | None = None

    class Config:
        """Конфігурація DTO."""

        from_attributes = True

    @pydantic.model_serializer()
    def serialize(self):
        """Сереалізувати DTO `TemplateVersionResponse`.

        Задає коректний порядок полів під час сереалізації.

        Returns:
          dict з сереалізованими атрибутами обʼєкту.
        """
        return {
            "tag": self.serialize_tag(self.tag),
            "message": self.message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
