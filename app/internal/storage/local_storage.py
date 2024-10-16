"""Модуль описує клас `LocalStorage` для операцій з
локальною файловою системою."""

import io
import pathlib
import shutil
import zipfile

from app.internal.storage import storage


class LocalStorage(storage.Storage):
    """Local filesystem storage with root directory enforcement."""

    def __init__(self, root: pathlib.Path):
        self._root = root.resolve()

    @property
    def root(self) -> pathlib.Path:
        return self._root

    def _resolve_path(self, path: pathlib.Path | None) -> pathlib.Path:
        """Resolve the path relative to the root and ensure it's within the root directory."""
        if path is None:
            return self.root

        resolved_path = path if path.is_absolute() else self.root / path
        resolved_path = resolved_path.resolve()

        if not resolved_path.is_relative_to(self.root):
            raise ValueError(
                f"Path is outside the root directory: {resolved_path}"
            )

        return resolved_path

    def save_file(
        self, data: io.BytesIO, path: pathlib.Path | None = None
    ) -> pathlib.Path:
        resolved_path = self._resolve_path(path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        with resolved_path.open("wb") as file:
            file.write(data.getbuffer())

        return resolved_path

    def load_file(self, path: pathlib.Path) -> io.BytesIO:
        resolved_path = self._resolve_path(path)
        with resolved_path.open("rb") as file:
            return io.BytesIO(file.read())

    def move_dir(
        self, source: pathlib.Path, destination: pathlib.Path | None = None
    ) -> pathlib.Path:
        source_resolved = self._resolve_path(source)
        destination_resolved = self._resolve_path(destination)

        if not source_resolved.exists() or not source_resolved.is_dir():
            raise FileNotFoundError(
                f"Source directory does not exist: {source_resolved}"
            )

        destination_resolved.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_resolved), str(destination_resolved))

        return destination_resolved

    def move_file(
        self, source: pathlib.Path, destination: pathlib.Path | None = None
    ) -> pathlib.Path:
        source_resolved = self._resolve_path(source)
        destination_resolved = self._resolve_path(destination)

        if not source_resolved.exists() or not source_resolved.is_file():
            raise FileNotFoundError(
                f"Source file does not exist: {source_resolved}"
            )

        destination_resolved.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_resolved), str(destination_resolved))

        return destination_resolved

    def delete(self, path: pathlib.Path) -> None:
        resolved_path = self._resolve_path(path)
        if resolved_path.is_dir():
            shutil.rmtree(resolved_path)
        elif resolved_path.is_file():
            resolved_path.unlink()
        else:
            raise FileNotFoundError(
                f"Path does not exist or is not a file/directory: {resolved_path}"
            )

    def is_file(self, path: pathlib.Path) -> bool:
        resolved_path = self._resolve_path(path)
        return resolved_path.is_file()

    def is_dir(self, path: pathlib.Path) -> bool:
        resolved_path = self._resolve_path(path)
        return resolved_path.is_dir()

    def listdir(self, path: pathlib.Path | None = None) -> list[pathlib.Path]:
        resolved_path = self._resolve_path(path)
        if not resolved_path.is_dir():
            raise FileNotFoundError(f"Is not a directory: {resolved_path}")

        return list(resolved_path.iterdir())

    def extract_zip(
        self, zip_path: pathlib.Path, destination: pathlib.Path | None = None
    ) -> pathlib.Path:
        zip_resolved = self._resolve_path(zip_path)
        destination_resolved = self._resolve_path(destination)

        with zipfile.ZipFile(zip_resolved, "r") as zip_file:
            for member in zip_file.namelist():
                if member.startswith("__MACOSX/"):
                    continue
                zip_file.extract(member, destination_resolved)

        return destination_resolved

    # TODO: think about deleting this method because LocaStorage.load_file can be used instead
    def load_zip(self, zip_path: pathlib.Path) -> io.BytesIO:
        zip_resolved = self._resolve_path(zip_path)
        with open(zip_resolved, "rb") as f:
            zip_bytes = f.read()

        zip_bytesio = io.BytesIO(zip_bytes)
        zip_bytesio.seek(0)
        return zip_bytesio

    def load_dir_as_zip(self, dir_path: pathlib.Path) -> io.BytesIO:
        dir_resolved = self._resolve_path(dir_path)
        if not self.exists(dir_resolved):
            raise FileNotFoundError(
                f"Path does not exist or is not a file/directory: {dir_resolved}"
            )
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in dir_resolved.rglob("*"):
                if file_path.is_file():
                    zip_file.write(
                        file_path, file_path.relative_to(dir_resolved)
                    )

        zip_buffer.seek(0)
        return zip_buffer

    # TODO: make private method for extracting zip files
    def save_dir(
        self, zip_bytes: io.BytesIO, path: pathlib.Path | None = None
    ) -> pathlib.Path:
        resolved_path = self._resolve_path(path)
        self.mkdir(resolved_path)

        root_name = None

        with zipfile.ZipFile(zip_bytes, "r") as zip_file:
            zip_namelist = zip_file.namelist()
            top_level_dirs = {
                pathlib.Path(name).parts[0]
                for name in zip_namelist
                if not name.startswith("__MACOSX/")
            }

            if len(top_level_dirs) == 1:
                root_name = next(iter(top_level_dirs))
            else:
                root_name = None
            for member in zip_namelist:
                if member.startswith("__MACOSX/"):
                    continue
                zip_file.extract(member, resolved_path)

        if root_name:
            return resolved_path / root_name

        return resolved_path

    def exists(self, path: pathlib.Path) -> bool:
        resolved_path = self._resolve_path(path)
        return resolved_path.exists()

    def mkdir(self, path: pathlib.Path) -> pathlib.Path:
        resolved_path = self._resolve_path(path)
        resolved_path.mkdir(parents=True, exist_ok=True)
        return resolved_path
