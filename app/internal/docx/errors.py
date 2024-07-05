"""Перелік помилок пакету `docx`."""


class PreparePrefixError(Exception):
    """Помилка під час обробки префіксного ключа тіла для генерації."""


class ZeroPrefixValueError(Exception):
    """Помилка в разі передачі до генератора префіксного
    ключа з нульовим значенням."""


class DocumentGenerationError(Exception):
    """Помилка генератора документів."""
