import io
import pathlib
import zipfile

import pytest

from app.internal import storage as storage_module


def test_save_file(storage: storage_module.Storage, tmp_path: pathlib.Path):
    data = io.BytesIO(b"test content")
    path = tmp_path / "test_dir" / "test_file.txt"

    saved_path = storage.save_file(data, path)

    assert saved_path.exists()
    assert path == saved_path
    assert saved_path.read_text() == "test content"


def test_load_file(storage: storage_module.Storage, tmp_path: pathlib.Path):
    data = io.BytesIO(b"test content")
    path = tmp_path / "test_dir" / "test_file.txt"
    saved_file_path = storage.save_file(data, path)

    loaded_data = storage.load_file(saved_file_path)

    assert loaded_data.getvalue() == b"test content"


def test_load_file_doesnt_exist(
    storage: storage_module.Storage, tmp_path: pathlib.Path
):
    file_path = tmp_path / "nontexistent.txt"
    with pytest.raises(FileNotFoundError):
        storage.load_file(file_path)


def test_load_file_outside_root(
    storage: storage_module.Storage, project_directory: pathlib.Path
):
    dockerfile = project_directory / "Dockerfile"
    with pytest.raises(ValueError, match="Path is outside the root directory:"):
        storage.load_file(dockerfile)


def test_move_file(storage: storage_module.Storage, tmp_path: pathlib.Path):
    data = io.BytesIO(b"test content")
    src_path = tmp_path / "test_dir" / "test_file.txt"
    storage.save_file(data, src_path)

    dst_path = pathlib.Path("test_dir_moved/test_file.txt")
    moved_path = storage.move_file(src_path, dst_path)

    assert moved_path.exists()
    assert not src_path.exists()
    with pytest.raises(FileNotFoundError):
        storage.load_file(src_path)
    assert moved_path.read_text() == "test content"


def test_move_dir(storage: storage_module.Storage, tmp_path: pathlib.Path):
    src_dir = tmp_path / "test_dir"
    src_dir.mkdir()
    src_file = src_dir / "test_file.txt"
    src_file.write_text("test content")

    dst_dir = pathlib.Path("test_dir_moved")
    moved_dir = storage.move_dir(src_dir, dst_dir)

    assert moved_dir.exists()
    assert (moved_dir / "test_file.txt").exists()
    assert (moved_dir / "test_file.txt").read_text() == "test content"
    assert not src_dir.exists()

    with pytest.raises(FileNotFoundError):
        storage.move_dir(src_dir, dst_dir)


def test_delete_file(storage: storage_module.Storage, tmp_path: pathlib.Path):
    data = io.BytesIO(b"test content")
    path = tmp_path / "test_file.txt"
    storage.save_file(data, path)

    storage.delete(path)

    assert not path.exists()
    with pytest.raises(FileNotFoundError):
        storage.load_file(path)


def test_delete_dir(storage: storage_module.Storage, tmp_path: pathlib.Path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    file_path = dir_path / "test_file.txt"
    file_path.write_text("test content")

    storage.delete(dir_path)

    assert not dir_path.exists()
    with pytest.raises(FileNotFoundError):
        storage.delete(dir_path)


def test_is_file(storage: storage_module.Storage):
    data = io.BytesIO(b"test content")
    file_path = pathlib.Path("test_file.txt")
    storage.save_file(data, file_path)

    assert storage.is_file(file_path)

    nontexsistent_path = pathlib.Path("non_existent_file.txt")
    assert not storage.is_file(nontexsistent_path)
    assert not storage.exists(nontexsistent_path)
    with pytest.raises(FileNotFoundError):
        storage.load_file(nontexsistent_path)


def test_is_dir(storage: storage_module.Storage):
    dir_path = pathlib.Path("test_dir")
    storage.mkdir(dir_path)

    assert storage.is_dir(dir_path)
    assert not storage.is_dir(pathlib.Path("non_existent_dir"))


def test_listdir(storage: storage_module.Storage, tmp_path: pathlib.Path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    (dir_path / "file1.txt").write_text("content1")
    (dir_path / "file2.txt").write_text("content2")

    files = storage.listdir(dir_path)

    assert len(files) == 2
    assert set(f.name for f in files) == {"file1.txt", "file2.txt"}

    nonexistent_path = pathlib.Path("non_existent_dir")
    with pytest.raises(FileNotFoundError):
        storage.listdir(nonexistent_path)


def test_extract_zip(storage: storage_module.Storage, tmp_path: pathlib.Path):
    zip_path = tmp_path / "test.zip"
    zip_content = io.BytesIO()
    with zipfile.ZipFile(zip_content, "w") as zip_file:
        zip_file.writestr("file1.txt", "content1")
        zip_file.writestr("file2.txt", "content2")

    zip_content.seek(0)
    with zip_path.open("wb") as f:
        f.write(zip_content.read())

    extracted_path = storage.extract_zip(zip_path, pathlib.Path("extracted"))

    assert (extracted_path / "file1.txt").exists()
    assert (extracted_path / "file2.txt").exists()

    nonexistent_zip = pathlib.Path("non_existent.zip")
    with pytest.raises(FileNotFoundError):
        storage.extract_zip(nonexistent_zip, pathlib.Path("extracted"))


def test_load_zip(storage: storage_module.Storage, tmp_path: pathlib.Path):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zip_file:
        zip_file.writestr("file1.txt", "content1")
        zip_file.writestr("file2.txt", "content2")

    zip_bytes = storage.load_zip(zip_path)

    with zipfile.ZipFile(zip_bytes) as zip_file:
        assert zip_file.read("file1.txt") == b"content1"
        assert zip_file.read("file2.txt") == b"content2"

    nonexistent_zip = pathlib.Path("non_existent.zip")
    with pytest.raises(FileNotFoundError):
        storage.load_zip(nonexistent_zip)


def test_load_dir_as_zip(
    storage: storage_module.Storage, tmp_path: pathlib.Path
):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()
    (dir_path / "file1.txt").write_text("content1")
    (dir_path / "file2.txt").write_text("content2")

    zip_bytes = storage.load_dir_as_zip(dir_path)

    with zipfile.ZipFile(zip_bytes) as zip_file:
        assert zip_file.read("file1.txt") == b"content1"
        assert zip_file.read("file2.txt") == b"content2"

    nonexistent_path = tmp_path / "non_existent_dir"
    with pytest.raises(FileNotFoundError):
        storage.load_dir_as_zip(nonexistent_path)


def test_save_dir(storage: storage_module.Storage):
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zip_file:
        zip_file.writestr("file1.txt", "content1")
        zip_file.writestr("file2.txt", "content2")

    zip_bytes.seek(0)
    destination = pathlib.Path("saved_dir")
    saved_path = storage.save_dir(zip_bytes, destination)
    print(saved_path)

    assert (saved_path / "file1.txt").exists()
    assert (saved_path / "file2.txt").exists()
    assert (saved_path / "file1.txt").read_text() == "content1"


def test_exists(storage: storage_module.Storage, tmp_path: pathlib.Path):
    dir_path = tmp_path / "test_dir"
    dir_path.mkdir()

    assert storage.exists(dir_path)
    assert not storage.exists(pathlib.Path("non_existent_dir"))
