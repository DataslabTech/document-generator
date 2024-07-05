"""Модуль надає шаблони для регулярних виразів."""

import re

url_pattern = re.compile(r"^(http|https|ftp)://[^\s/$.?#].[^\s]*$")


def is_url(string: str) -> bool:
    """Перевірити, чи є рядок валідним URL.

    Args:
      string: вхідний рядок.

    Returns:
      `True`, якщо рядок відповідає шаблону URL, `False` інакше.
    """
    return bool(re.match(url_pattern, string))
