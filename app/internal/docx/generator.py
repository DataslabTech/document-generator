"""Модуль описує інтерфейс `DocGenerator` та клас `DocxDocGenerator`."""

import io
import pathlib
import uuid
from abc import ABC, abstractmethod
from typing import Any, Callable

import docx.shared as docx_shared
import docxtpl
import pyqrcode

from app.core import config
from app.internal import storage, webclient
from app.internal.docx import const, errors, filters, formulas, models, regexp


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
            str, Callable[[docxtpl.DocxTemplate, dict[str, Any]], Any]
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
        context = self._prepare_context(doc, raw_context)
        doc.render(context, filters.env, autoescape=autoescape)

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

            self._process_tpl_key(doc, new_context, attr)

            if isinstance(value, dict):
                self._process_tpl_dict(doc, new_context, attr)

            elif isinstance(value, list):
                self._process_tpl_list(doc, new_context, attr)

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
                doc, attr.key, attr.value
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
        context[attr.key] = []
        for item in attr.value:
            if isinstance(item, dict):
                context[attr.key].append({})
                self._process_tpl_data(doc, item, context[attr.key][-1])  # type: ignore # noqa
            else:
                context[attr.key].append(item)

    def _prepare_prefix(
        self, doc: docxtpl.DocxTemplate, key: str, value: Any
    ) -> tuple[str, Any]:
        prefix, var_name = key.split(const.DIVIDER)
        return var_name, self._prefix_methods[prefix](doc, value)

    def _prepare_image(
        self, doc: docxtpl.DocxTemplate, data: dict[str, Any]
    ) -> docxtpl.InlineImage:
        image_data = models.DocxInlineImage(**data)
        image_file = self._get_image_from_source(image_data.source)
        image = self._build_inline_image(
            doc, image_file, image_data.width, image_data.height
        )
        return image

    def _prepare_rich_text(
        self, doc: docxtpl.DocxTemplate, data: dict[str, Any]
    ) -> docxtpl.RichText:
        rich_text_data = models.DocxRichText(**data)
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
        self, doc: docxtpl.DocxTemplate, data: dict[str, Any]
    ) -> docxtpl.InlineImage:
        print(data)
        qrcode_data = models.DocxQrCode.model_validate(data)
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
        self, doc: docxtpl.DocxTemplate, data: dict[str, Any]
    ):
        image_file = self._get_image_from_source(data["source"])
        doc.replace_media(data["dummy"], image_file)  # type: ignore

    def _prepare_formula(
        self, doc: docxtpl.DocxTemplate, data: dict[str, Any]
    ) -> docxtpl.Subdoc:
        formula = formulas.latex_to_word(r"" + data["formula"])
        equation_doc = doc.new_subdoc()  # type: ignore
        p = equation_doc.add_paragraph()
        p._element.append(formula)
        old_get_xml = equation_doc._get_xml  # type: ignore

        def new_get_xml():
            return old_get_xml().replace(*formulas.format_xml_replace())

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
        print(doc.__dict__)
        return docxtpl.InlineImage(
            doc, str(img_path), height=height, width=width
        )

    def _get_image_from_source(self, source: str) -> pathlib.Path:
        if regexp.is_url(source):
            try:
                image_file = webclient.download_image(source)
                image_path = (
                    pathlib.Path(config.settings.LOCAL_STORAGE_TMP_PATH)
                    / image_file.name
                )
                file_path = self._tmp_storage.save_file(
                    image_path, image_file.file_bytes
                )
                return file_path
            except webclient.DownloadFileError as e:
                raise errors.PreparePrefixError(
                    f"Cannot download image. Reason: {e}"
                )
        else:
            raise errors.PreparePrefixError("Image source must be a valid URL")
