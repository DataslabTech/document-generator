"""Модуль описує інтерфейс Storage для доступу до сховища."""

import io
import pathlib
from abc import ABC, abstractmethod


class Storage(ABC):
    """Сховище даних."""

    @abstractmethod
    def save_file(self, path: pathlib.Path, data: io.BytesIO) -> pathlib.Path:
        """Зберегти байтовий потік файлу за шляхом.

        Args:
          path: шлях, за яким слід зберегти файл.
          data: байтова послідовність файлу.

        Returns:
          Шлях до новоствореного файлу.
        """

    @abstractmethod
    def load_file(self, path: pathlib.Path) -> io.BytesIO:
        """Завантажити файл в байтовий потік за шляхом.

        Args:
          path: шлях, за яким слід зберегти файл.

        Returns:
          Байтова послідовність файлу.

        Raises:
          FileNotFoundError: Файл не знайдено.
        """

    @abstractmethod
    def move_dir(
        self, source: pathlib.Path, destination: pathlib.Path
    ) -> pathlib.Path:
        """Перемістити директорію в інше місце.

        Args:
          source: Поточний шлях директорії.
          destination: Шлях, куди треба перемістити директорію.

        Returns:
          Шлях до переміщеної директорії.

        Raises:
          FileNotFoundError: Шлях не знайдено.
        """

    @abstractmethod
    def move_file(
        self, source: pathlib.Path, destination: pathlib.Path
    ) -> pathlib.Path:
        """Перемістити файл в інше місце.

        Args:
          source: Поточний шлях до файлу.
          destination: Шлях, куди треба перемістити файл.

        Returns:
          Шлях до переміщеного файлу.

        Raises:
          FileNotFoundError: Шлях не знайдено.
        """

    @abstractmethod
    def delete(self, path: pathlib.Path) -> None:
        """Видалити файл або директорію.

        Args:
          path: Шлях обʼєкту на видалення.

        Raises:
          FileNotFoundError: Шлях не знайдено.
        """

    @abstractmethod
    def is_file(self, path: pathlib.Path) -> bool:
        """Перевірити, чи є обʼєкт за шляхом файлом.

        Args:
          path: Шлях обʼєкту.

        Returns:
          `True`, якщо обʼєкт - це файл, `False` інакше.

        Raises:
          FileNotFoundError: Шлях не знайдено.
        """

    @abstractmethod
    def is_dir(self, path: pathlib.Path) -> bool:
        """Перевірити, чи є обʼєкт за шляхом директорією.

        Args:
          path: Шлях обʼєкту.

        Returns:
          `True`, якщо обʼєкт - це директорія, `False` інакше.

        Raises:
          FileNotFoundError: Шлях не знайдено.
        """

    @abstractmethod
    def listdir(self, path: pathlib.Path) -> list[pathlib.Path]:
        """Отримати список обʼєктів в директорії.

        Args:
          path: Шлях до директорії.

        Returns: Список шляхів до обʼєктів директорії.

        Raises:
          FileNotFoundError: Шлях не знайдено.
        """

    @abstractmethod
    def mkdir(self, path: pathlib.Path) -> pathlib.Path:
        """
        Створити директорію

        Args:
          path: Шлях до директорії, що має бути створена.

        Returns:
          Шлях до нової директорії.
        """

    @abstractmethod
    def exists(self, path: pathlib.Path) -> bool:
        """Перевірити, чи існує обʼєкт за шляхом.

        Args:
          path: Шлях обʼєкту.

        Returns:
          `True`, якщо обʼєкт існує, `False` інакше.
        """

    @abstractmethod
    def save_dir(
        self, zip_bytes: io.BytesIO, path: pathlib.Path
    ) -> pathlib.Path:
        """Зберегти директорію з байтового потоку `zip` за шляхом.

        Args:
          zip_bytes: Байтовий потік `zip` архіву.
          path: Директорія, куди збережеться інформація.

        Returns:
          Шлях до новоствореної директорії.
        """

    @abstractmethod
    def extract_zip(
        self, zip_path: pathlib.Path, destination: pathlib.Path
    ) -> pathlib.Path:
        """Розпакувати `zip` архів.

        Args:
          zip_path: Шлях до `zip` врхіву.
          destination: Директорія, куди розпакується архів.

        Returns:
          Шлях до розпакованої директорії.
        """

    @abstractmethod
    def load_zip(self, zip_path: pathlib.Path) -> io.BytesIO:
        """Завантажити `zip` архів в байтовий потік.

        Args:
          zip_path: Шлях до `zip` врхіву.

        Returns:
          Байтовий потік `zip` архіву.

        Raises:
          FileNotFoundError: Шлях не знайдено.
        """

    @abstractmethod
    def load_dir_as_zip(self, dir_path: pathlib.Path) -> io.BytesIO:
        """Запакувати директорію в байтовий потік `zip` архіву

        Args:
          dir_path: Шлях до директорії.

        Returns:
          Байтовий потік `zip` архіву.

        Raises:
          FileNotFoundError: Шлях не знайдено.
        """
