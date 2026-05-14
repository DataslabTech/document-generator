"""Перелік DTO для формування контексту генерації документу."""

import enum
from typing import Any

import pydantic

from app.internal.docx import errors


class ContextAttribute(pydantic.BaseModel):
    """Ключ-значення контексту генерації документу.

    Attributes:
        key: Ключ.
        value: Значення.
    """

    key: str
    value: Any


def _validate_image_dimension(value: Any) -> Any:
    if value == 0:
        return None
    return value


class PrefixValue(pydantic.BaseModel):
    """Ключ-значення префіксного значення для генерації документу.

    Attributes:
        key: Ключ.
        value: Значення.
    """

    key: str
    value: dict[str, Any]


class DocxInlineImage(pydantic.BaseModel):
    """DTO для ключа контексту `IMG|<KEY>`

    Attributes:
        source: Посилання на зображення.
        width: Ширина зображення (в см).
        height: Висота зображення (в см).
    """

    source: str
    width: int | None = None
    height: int | None = None

    @pydantic.field_validator("source", mode="before")
    @classmethod
    def _validate_image_source(cls, value: Any):
        if value == "":
            raise errors.ZeroPrefixValueError("Empty image source passed")
        return value

    @pydantic.field_validator("width", mode="before")
    @classmethod
    def _validate_width(cls, value: Any):
        return _validate_image_dimension(value)

    @pydantic.field_validator("height", mode="before")
    @classmethod
    def _validate_height(cls, value: Any):
        return _validate_image_dimension(value)


class QrErrorType(enum.Enum):
    """Перелік типів помилок QR-коду."""

    L = "L"
    M = "M"
    Q = "Q"
    H = "H"


class DocxQrCode(pydantic.BaseModel):
    """DTO для ключа контексту `QR|<KEY>`

    Attributes:
        data: Дані для кодування.
        padding: Розмір тихої зони навколо QR-коду в модулях.
        width: Ширина зображення (в см).
    """

    data: str
    version: int | None = pydantic.Field(None, ge=1, le=40)
    error: QrErrorType = QrErrorType.M
    width: int | None = None
    padding: int = pydantic.Field(0, ge=0)

    @pydantic.field_validator("data", mode="before")
    @classmethod
    def _validate_image_source(cls, value: Any):
        if value == "":
            raise errors.ZeroPrefixValueError("Empty data passed")
        return value

    @pydantic.field_validator("width", mode="before")
    @classmethod
    def _validate_width(cls, value: Any):
        return _validate_image_dimension(value)


class BarcodeType(enum.Enum):
    """Перелік типів штрихкодів."""

    CODE128 = "code128"
    EAN13 = "ean13"
    EAN8 = "ean8"


class DocxBarcode(pydantic.BaseModel):
    """DTO для ключа контексту `BARCODE|<KEY>`

    Attributes:
        data: Дані для кодування.
        type: Тип штрихкоду.
        width: Ширина зображення (в см).
        height: Висота зображення (в см).
        padding: Відступи навколо штрихкоду в мм.
        show_text: Додати текстове представлення під штрихкодом.
    """

    data: str
    type: BarcodeType = BarcodeType.CODE128
    width: int | None = None
    height: int | None = None
    padding: float = pydantic.Field(0, ge=0)
    show_text: bool = False

    @pydantic.field_validator("data", mode="before")
    @classmethod
    def _validate_data(cls, value: Any):
        if value == "":
            raise errors.ZeroPrefixValueError("Empty data passed")
        return value

    @pydantic.field_validator("width", "height", mode="before")
    @classmethod
    def _validate_dimensions(cls, value: Any):
        return _validate_image_dimension(value)


class RichTextUnderline(enum.Enum):
    """Перелік типів нижнього підкреслення тексту."""

    SINGLE = "single"
    DOUBLE = "double"
    THICK = "thick"
    DOTTED = "dotted"
    DASH = "dash"
    DOTDASH = "dotDash"
    DOTDOTDASH = "dotDotDash"
    WAVE = "wave"


class DocxRichTextAddition(pydantic.BaseModel):
    """Компонент RichText"""

    text: str
    style: str | None = None
    color: str | None = None
    highlight: str | None = None
    size: int | None = None
    subscript: bool = False
    superscript: bool = False
    bold: bool = False
    italic: bool = False
    underline: RichTextUnderline | None = None
    strike: bool = False
    font: str | None = None
    url_id: str | None = None


class DocxRichText(pydantic.BaseModel):
    """DTO для ключа контексту `RICH|<KEY>`

    Attributes:
        base_text: Текст для форматування.
        adds: Список форматувань RichText для застосування.
    """

    base_text: str
    adds: list[DocxRichTextAddition]


class DocxHtml(pydantic.BaseModel):
    """DTO для ключа контексту `HTML|<KEY>`

    Attributes:
        html: HTML-код для вставки в документ.
    """

    html: str
    font: str | None = None
    size: int | None = None
