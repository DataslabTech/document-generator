"""The module describes the Storage interface for accessing storage."""

import io
import pathlib
from abc import ABC, abstractmethod


class Storage(ABC):
    """Data storage."""

    @abstractmethod
    def save_file(self, path: pathlib.Path, data: io.BytesIO) -> pathlib.Path:
        """Save a byte stream of the file to a path.

        Args:
          path: the path where the file should be saved.
          data: byte sequence of the file.

        Returns:
          The path to the newly created file.
        """

    @abstractmethod
    def load_file(self, path: pathlib.Path) -> io.BytesIO:
        """Load a file into a byte stream from a path.

        Args:
          path: the path from where the file should be loaded.

        Returns:
          Byte sequence of the file.

        Raises:
          FileNotFoundError: File not found.
        """

    @abstractmethod
    def move_dir(
        self, source: pathlib.Path, destination: pathlib.Path
    ) -> pathlib.Path:
        """Move a directory to a new location.

        Args:
          source: Current path of the directory.
          destination: The path where the directory should be moved.

        Returns:
          Path to the moved directory.

        Raises:
          FileNotFoundError: Path not found.
        """

    @abstractmethod
    def move_file(
        self, source: pathlib.Path, destination: pathlib.Path
    ) -> pathlib.Path:
        """Move a file to a new location.

        Args:
          source: Current path of the file.
          destination: The path where the file should be moved.

        Returns:
          Path to the moved file.

        Raises:
          FileNotFoundError: Path not found.
        """

    @abstractmethod
    def delete(self, path: pathlib.Path) -> None:
        """Delete a file or directory.

        Args:
          path: Path of the object to be deleted.

        Raises:
          FileNotFoundError: Path not found.
        """

    @abstractmethod
    def is_file(self, path: pathlib.Path) -> bool:
        """Check if the object at the path is a file.

        Args:
          path: Path of the object.

        Returns:
          `True` if the object is a file, `False` otherwise.

        Raises:
          FileNotFoundError: Path not found.
        """

    @abstractmethod
    def is_dir(self, path: pathlib.Path) -> bool:
        """Check if the object at the path is a directory.

        Args:
          path: Path of the object.

        Returns:
          `True` if the object is a directory, `False` otherwise.

        Raises:
          FileNotFoundError: Path not found.
        """

    @abstractmethod
    def listdir(self, path: pathlib.Path) -> list[pathlib.Path]:
        """Get a list of objects in a directory.

        Args:
          path: Path to the directory.

        Returns:
          List of paths to the objects in the directory.

        Raises:
          FileNotFoundError: Path not found.
        """

    @abstractmethod
    def mkdir(self, path: pathlib.Path) -> pathlib.Path:
        """Create a directory.

        Args:
          path: Path of the directory to be created.

        Returns:
          Path to the newly created directory.
        """

    @abstractmethod
    def exists(self, path: pathlib.Path) -> bool:
        """Check if the object exists at the path.

        Args:
          path: Path of the object.

        Returns:
          `True` if the object exists, `False` otherwise.
        """

    @abstractmethod
    def save_dir(
        self, zip_bytes: io.BytesIO, path: pathlib.Path
    ) -> pathlib.Path:
        """Save a directory from a `zip` byte stream to a path.

        Args:
          zip_bytes: Byte stream of the `zip` archive.
          path: Directory where the data should be saved.

        Returns:
          Path to the newly created directory.
        """

    @abstractmethod
    def extract_zip(
        self, zip_path: pathlib.Path, destination: pathlib.Path
    ) -> pathlib.Path:
        """Extract a `zip` archive.

        Args:
          zip_path: Path to the `zip` archive.
          destination: Directory where the archive will be extracted.

        Returns:
          Path to the extracted directory.
        """

    @abstractmethod
    def load_zip(self, zip_path: pathlib.Path) -> io.BytesIO:
        """Load a `zip` archive into a byte stream.

        Args:
          zip_path: Path to the `zip` archive.

        Returns:
          Byte stream of the `zip` archive.

        Raises:
          FileNotFoundError: Path not found.
        """

    @abstractmethod
    def load_dir_as_zip(self, dir_path: pathlib.Path) -> io.BytesIO:
        """Package a directory into a `zip` byte stream.

        Args:
          dir_path: Path to the directory.

        Returns:
          Byte stream of the `zip` archive.

        Raises:
          FileNotFoundError: Path not found.
        """
