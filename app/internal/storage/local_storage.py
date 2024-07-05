"""Модуль описує клас `LocalStorage` для операцій з
локальною файловою системою."""

import io
import pathlib
import shutil
import zipfile

from app.internal.storage import storage


class LocalStorage(storage.Storage):
    """Сховище даних локальної файлової системи.

    Імплементація "Storage".
    """

    def save_file(self, path: pathlib.Path, data: io.BytesIO) -> pathlib.Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as file:
            file.write(data.getbuffer())

        return path

    def load_file(self, path: pathlib.Path) -> io.BytesIO:
        with path.open("rb") as file:
            return io.BytesIO(file.read())

    def move_dir(
        self, source: pathlib.Path, destination: pathlib.Path
    ) -> pathlib.Path:
        if not source.exists() or not source.is_dir():
            raise FileNotFoundError(
                f"Source directory does not exist: {source=}"
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

        return destination

    def move_file(
        self, source: pathlib.Path, destination: pathlib.Path
    ) -> pathlib.Path:
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(f"Source file does not exist: {source=}")

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

        return destination

    def delete(self, path: pathlib.Path) -> None:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()
        else:
            raise FileNotFoundError(
                f"Path does not exist or is not a file/directory: {path=}"
            )

    def is_file(self, path: pathlib.Path) -> bool:
        return path.is_file()

    def is_dir(self, path: pathlib.Path) -> bool:
        return path.is_dir()

    def listdir(self, path: pathlib.Path) -> list[pathlib.Path]:
        if not self.is_dir(path):
            raise FileNotFoundError(f"Is not a directory: {path=}")

        return list(path.iterdir())

    def extract_zip(
        self, zip_path: pathlib.Path, destination: pathlib.Path
    ) -> pathlib.Path:
        dir_name = zip_path.stem
        with zipfile.ZipFile(zip_path, "r") as zip_file:
            for member in zip_file.namelist():
                if member.startswith("__MACOSX/"):
                    continue
                zip_file.extract(member, destination)

        return destination / dir_name

    def load_zip(self, zip_path: pathlib.Path) -> io.BytesIO:
        zip_bytesio = io.BytesIO()

        with zipfile.ZipFile(zip_path, "r") as zip_file:
            for file_name in zip_file.namelist():
                file_content = zip_file.read(file_name)
                zip_bytesio.write(file_content)

        zip_bytesio.seek(0)

        return zip_bytesio

    def load_dir_as_zip(self, dir_path: pathlib.Path) -> io.BytesIO:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED
        ) as zip_file:
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    zip_file.write(file_path, file_path)

        zip_buffer.seek(0)
        return zip_buffer

    def save_dir(
        self, zip_bytes: io.BytesIO, path: pathlib.Path
    ) -> pathlib.Path:
        self.mkdir(path)

        with zipfile.ZipFile(zip_bytes, "r") as zip_ref:
            zip_members = zip_ref.namelist()
            zip_name = zip_members[0].strip("/")
            for member in zip_members:
                if member.startswith("__MACOSX/"):
                    continue
                zip_ref.extract(member, path)

        return path / zip_name

    def exists(self, path: pathlib.Path) -> bool:
        return path.exists()

    def mkdir(self, path: pathlib.Path) -> pathlib.Path:
        path.mkdir(parents=True, exist_ok=True)
        return path
