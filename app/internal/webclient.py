"""Модуль описує інструменти для HTTP запитів."""

import dataclasses
import io

import requests


class DownloadFileError(Exception):
    """Помилка під час завантаження файлу за URL."""


@dataclasses.dataclass
class DownloadedFile:
    """DTO для викачаних файлів за URL.

    Attributes:
        name: Назва файлу.
        file_bytes: Байтовий потік файлу.
    """

    name: str
    file_bytes: bytes


def download_file(url: str, filename: str | None = None) -> DownloadedFile:
    """Завантажує зображення за посиланням в байтову послідовність.

    Args:
      url: Посилання на зображення.
      filename: Назва файлу.

    Returns:
      DTO DownloadedFile.

    Raises:
        DownloadFileError: Помилка під час завантаження зображення.
    """
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        if filename is None:
            filename = url.split("/")[-1]
            if "." not in filename:
                content_type = response.headers.get("content-type")
                if content_type is None:
                    raise ValueError(
                        "Could not determine file extension from the"
                        " URL or content-type header."
                    )
                extension = content_type.split("/")[-1]
                filename = f"{filename}.{extension}"
        return DownloadedFile(name=filename, file_bytes=response.content)

    except ValueError as e:
        raise DownloadFileError(f"Invalid URL provided: {url}") from e
    except FileNotFoundError as e:
        raise DownloadFileError(
            f"Save directory does not exist: {filename}"
        ) from e
    except requests.exceptions.RequestException as e:
        raise DownloadFileError(f"Failed to download the file: {e}") from e
