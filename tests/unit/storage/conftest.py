import pathlib

import pytest

from app.internal import storage as storage_module


@pytest.fixture
def storage(tmp_path: pathlib.Path):
    """Fixture to provide storage.LocalStorage instance with a root in tmpdir."""
    root = pathlib.Path(tmp_path)
    return storage_module.LocalStorage(root)


@pytest.fixture(scope="session")
def project_directory() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent.parent.parent
