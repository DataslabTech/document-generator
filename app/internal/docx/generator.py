"""Модуль описує інтерфейс `DocGenerator` та клас `DocxDocGenerator`."""

import io
import pathlib
import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable

import docx.shared as docx_shared
import docxtpl
import jinja2
import pydantic
import pyqrcode

from app.core import config
from app.internal import storage, webclient
from app.internal.docx import const, errors, filters, formulas, models


class DocxGenerator(ABC):
    """Клас призначений для генерації `.docx` документів за наданою версією
    шаблону."""

    @abstractmethod
    def generate_bytes(
        self, template_stream: io.BytesIO, raw_context: dict[str, Any]
    ) -> io.BytesIO:
        """Згенерувати документ за шаблоном переданим контекстом.

        Args:
          template_stream: Байтовий потік шаблону документу.
          raw_context: Обʼєкт підстановки в шаблон.

        Returns:
          Байтовий потік згенерованого документу.
        Raises:
          DocumentGenerationError: Помилка під час генерації документу.
        """


class DoctplDocxGenerator(DocxGenerator):
    """Клас призначений для генерації `.docx` документів за наданою версією
    шаблону."""

    def __init__(self, tmp_storage: storage.Storage):
        self._tmp_storage = tmp_storage

        self._prefix_methods: dict[
            str, Callable[[docxtpl.DocxTemplate, models.PrefixValue], Any]
        ] = {
            const.IMG: self._prepare_image,
            const.MATH: self._prepare_formula,
            const.QR: self._prepare_qrcode,
            const.RICH: self._prepare_rich_text,
        }

    def generate_bytes(
        self, template_stream: io.BytesIO, raw_context: dict[str, Any]
    ) -> io.BytesIO:
        doc = self._get_doc(template_stream)
        self._generate(doc, raw_context)
        return self._save_bytes(doc)

    def _generate(
        self,
        doc: docxtpl.DocxTemplate,
        raw_context: dict[str, Any],
        autoescape: bool = True,
    ) -> None:
        try:
            context = self._prepare_context(doc, raw_context)
            doc.render(context, filters.env, autoescape=autoescape)
        except jinja2.exceptions.UndefinedError as e:
            raise errors.DocumentGenerationError(
                f"Key is not present in request body: {e}"
            )
        except TypeError as e:
            raise errors.DocumentGenerationError(
                f"Invalid template value type: {e}"
            )
        except errors.PreparePrefixError as e:
            raise errors.DocumentGenerationError(
                f"Invalid prefix key passed. {e}"
            ) from e

    def _get_doc(self, template_stream: io.BytesIO) -> docxtpl.DocxTemplate:
        return docxtpl.DocxTemplate(template_stream)

    def _save_bytes(
        self,
        doc: docxtpl.DocxTemplate,
    ) -> io.BytesIO:
        doc_bytes = io.BytesIO()
        doc.save(doc_bytes)  # type: ignore
        doc_bytes.seek(0)
        return doc_bytes

    @property
    def _supported_prefixes(self):
        return self._prefix_methods.keys()

    def _prepare_context(
        self, doc: docxtpl.DocxTemplate, raw_context: dict[str, Any]
    ) -> dict[str, Any]:
        new_context: dict[str, Any] = {}
        self._process_tpl_data(doc, raw_context, new_context)
        return new_context

    def _process_tpl_data(
        self,
        doc: docxtpl.DocxTemplate,
        raw_context: dict[str, Any],
        new_context: dict[str, Any],
    ):
        for key, value in raw_context.items():
            attr = models.ContextAttribute(key=key, value=value)

            if isinstance(value, dict):
                self._process_tpl_dict(doc, new_context, attr)

            elif isinstance(value, list):
                self._process_tpl_list(doc, new_context, attr)

            else:
                self._process_tpl_key(doc, new_context, attr)

    def _process_tpl_key(
        self,
        doc: docxtpl.DocxTemplate,
        context: dict[str, Any],
        attr: models.ContextAttribute,
    ):
        if const.DIVIDER not in attr.key:
            context[attr.key] = attr.value
            return

        try:
            new_key, new_value = self._prepare_prefix(
                doc, models.PrefixValue(key=attr.key, value=attr.value)
            )
            context[new_key] = new_value
        except errors.ZeroPrefixValueError:
            return

    def _process_tpl_dict(
        self,
        doc: docxtpl.DocxTemplate,
        context: dict[str, Any],
        attr: models.ContextAttribute,
    ):
        context[attr.key] = {}
        self._process_tpl_data(doc, attr.value, context[attr.key])

    def _process_tpl_list(
        self,
        doc: docxtpl.DocxTemplate,
        context: dict[str, Any],
        attr: models.ContextAttribute,
    ):
        if const.DIVIDER in attr.key:
            new_key = self._split_prefix_key(attr.key)[1]
            context[new_key] = []
            for item in attr.value:
                _, new_value = self._prepare_prefix(
                    doc, models.PrefixValue(key=attr.key, value=item)
                )
                context[new_key].append(new_value)
        else:
            context[attr.key] = []
            for item in attr.value:
                if isinstance(item, dict):
                    context[attr.key].append({})
                    self._process_tpl_data(doc, item, context[attr.key][-1])  # type: ignore
                else:
                    context[attr.key].append(item)

    def _split_prefix_key(self, key: str) -> tuple[str, str]:

        key_split = key.split(const.DIVIDER)
        if len(key_split) != 2:
            raise errors.PreparePrefixError(f"Invalid prefix key name: {key}")
        return (key_split[0], key_split[1])

    def _prepare_prefix(
        self, doc: docxtpl.DocxTemplate, prefix_value: models.PrefixValue
    ) -> tuple[str, Any]:
        prefix, var_name = self._split_prefix_key(prefix_value.key)
        return var_name, self._prefix_methods[prefix](doc, prefix_value)

    def _prepare_image(
        self, doc: docxtpl.DocxTemplate, prefix_value: models.PrefixValue
    ) -> docxtpl.InlineImage:
        try:
            image_data = models.DocxInlineImage(**prefix_value.value)
            image_file = self._get_image_from_source(image_data.source)
            image = self._build_inline_image(
                doc, image_file, image_data.width, image_data.height
            )
            return image
        except (webclient.DownloadFileError, pydantic.ValidationError) as e:
            raise errors.PreparePrefixError(
                f"Cannot prepare prefix {prefix_value.key}. Reason: {e}"
            )

    def _prepare_rich_text(
        self, doc: docxtpl.DocxTemplate, prefix_value: models.PrefixValue
    ) -> docxtpl.RichText:
        rich_text_data = models.DocxRichText(**prefix_value.value)
        rt = docxtpl.RichText(rich_text_data.base_text)
        for addition in rich_text_data.adds:
            rt.add(  # type: ignore
                addition.text,
                style=addition.style,
                color=addition.color,
                highlight=addition.highlight,
                size=addition.size,
                subscript=addition.subscript,
                superscript=addition.superscript,
                bold=addition.bold,
                italic=addition.italic,
                underline=addition.underline,  # type: ignore
                strike=addition.strike,
                font=addition.font,
                url_id=(
                    doc.build_url_id(addition.url_id)  # type: ignore
                    if addition.url_id
                    else None
                ),
            )
        return rt

    def _prepare_qrcode(
        self, doc: docxtpl.DocxTemplate, prefix_value: models.PrefixValue
    ) -> docxtpl.InlineImage:
        qrcode_data = models.DocxQrCode.model_validate(prefix_value.value)
        encoded_data = pyqrcode.create(qrcode_data.data, encoding="utf-8")  # type: ignore # noqa

        qr_filename = (
            pathlib.Path(config.settings.LOCAL_STORAGE_TEMPLATE_PATH)
            / f"qrcode_{uuid.uuid4()}.png"
        )

        encoded_data.png(qr_filename, scale=8)  # type: ignore
        return self._build_inline_image(
            doc, qr_filename, width=qrcode_data.width
        )

    def _prepare_header_footer_image(
        self, doc: docxtpl.DocxTemplate, prefix_value: models.PrefixValue
    ):
        image_file = self._get_image_from_source(prefix_value.value["source"])
        doc.replace_media(prefix_value.value["dummy"], image_file)  # type: ignore

    def _prepare_formula(
        self, doc: docxtpl.DocxTemplate, prefix_value: models.PrefixValue
    ) -> docxtpl.Subdoc:
        formula = formulas.latex_to_word(r"" + prefix_value.value["formula"])
        equation_doc = doc.new_subdoc()  # type: ignore
        p = equation_doc.add_paragraph()
        p._element.append(formula)
        old_get_xml = equation_doc._get_xml  # type: ignore

        def new_get_xml() -> Any:
            return old_get_xml().replace(*formulas.format_xml_replace())  # type: ignore

        equation_doc._get_xml = new_get_xml  # type: ignore
        return equation_doc

    def _build_inline_image(
        self,
        doc: docxtpl.DocxTemplate,
        img_path: pathlib.Path,
        width: int | None = None,
        height: int | None = None,
    ) -> docxtpl.InlineImage:
        width = docx_shared.Mm(width) if width is not None else None
        height = docx_shared.Mm(height) if height is not None else None

        return docxtpl.InlineImage(
            doc, str(img_path), height=height, width=width
        )

    def _get_image_from_source(self, source: str) -> pathlib.Path:
        image_file = webclient.download_file(source)
        image_path = (
            pathlib.Path(config.settings.LOCAL_STORAGE_TMP_PATH)
            / image_file.name
        )
        file_path = self._tmp_storage.save_file(
            image_file.file_bytes, image_path
        )
        return file_path
