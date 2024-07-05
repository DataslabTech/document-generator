"""Пакет `docx` надає інструменти для генерації документів."""

from app.internal.docx import errors
from app.internal.docx.generator import DoctplDocxGenerator, DocxGenerator

__all__ = ["DocxGenerator", "DoctplDocxGenerator", "errors"]
