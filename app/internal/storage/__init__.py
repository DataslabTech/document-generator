"""Пакет Storage надає функціонал для керування файловою системою."""

from app.internal.storage.local_storage import LocalStorage
from app.internal.storage.storage import Storage

__all__ = ["LocalStorage", "Storage"]
