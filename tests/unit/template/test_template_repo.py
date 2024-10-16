import io
import pathlib
import uuid

import pytest

from app.internal import storage
from app.internal.template import errors, factory, meta
from app.internal.template import repo as base_repo
from app.internal.template import schema
from app.internal.template import storage_repo as repo
from app.internal.template import validator
from tests import factory as test_factory
from tests.mock import template_mock


@pytest.fixture(scope="function")
def mem_cache() -> repo.TemplateCache:
    return repo.MemoryTemplateCache()


@pytest.fixture(scope="function")
def template_storage(tmp_path: pathlib.Path) -> storage.Storage:
    tpl_path = tmp_path / "templates"
    tpl_path.mkdir()
    return storage.LocalStorage(tpl_path)


@pytest.fixture(scope="function")
def tmp_storage(tmp_path: pathlib.Path) -> storage.Storage:
    tmp_storage_path = tmp_path / "tmp"
    tmp_storage_path.mkdir()
    return storage.LocalStorage(tmp_storage_path)


@pytest.fixture(scope="function")
def tpl_factory() -> factory.TemplateFactory:
    return template_mock.MockTemplateFactory()


@pytest.fixture(scope="function")
def tpl_validator() -> validator.TemplateValidator:
    return template_mock.MockTemplateValidator()


@pytest.fixture(scope="function")
def template_repo(
    mem_cache: repo.TemplateCache,
    tmp_storage: storage.Storage,
    template_storage: storage.Storage,
    tpl_factory: factory.TemplateFactory,
    tpl_validator: validator.TemplateValidator,
) -> base_repo.TemplateRepository:
    return repo.StorageTemplateRepository(
        file_storage=template_storage,
        tmp_storage=tmp_storage,
        tmp_validator=tpl_validator,
        factory=tpl_factory,
        cache=mem_cache,
    )


@pytest.fixture(scope="function")
def template_repo_with_storage_validator(
    mem_cache: repo.TemplateCache,
    tmp_storage: storage.Storage,
    template_storage: storage.Storage,
    tpl_factory: factory.TemplateFactory,
) -> base_repo.TemplateRepository:
    return repo.StorageTemplateRepository(
        file_storage=template_storage,
        tmp_storage=tmp_storage,
        tmp_validator=validator.StorageTemplateValidator(tmp_storage),
        factory=tpl_factory,
        cache=mem_cache,
    )


def test_mem_cache(mem_cache: repo.TemplateCache):
    assert len(mem_cache.list()) == 0

    template1 = test_factory.get_template([])
    template2 = test_factory.get_template([])

    mem_cache.add(template1)
    mem_cache.add(template2)

    assert len(mem_cache.list()) == 2

    assert mem_cache.get(template1.id) == template1

    nonexistent_template_id = uuid.uuid4()
    nonexistent_template = mem_cache.get(nonexistent_template_id)

    assert nonexistent_template is None


class TestStorageTemplateRepo:
    def test_create_from_path(
        self, template_repo: base_repo.TemplateRepository
    ):
        template_path = pathlib.Path("tests/unit/template/template1")
        template = template_repo.create_from_path(template_path)

        assert template_repo.get(template.id) is not None
        assert template_repo.get(uuid.uuid4()) is None

    def test_create(
        self,
        template_repo: base_repo.TemplateRepository,
    ):
        create_schema = schema.TemplateCreate(
            title="template", description="description", labels=[]
        )
        template = template_repo.create(create_schema)
        template_path = pathlib.Path(str(template.id))

        assert template_repo._file_storage.is_dir(template_path)
        assert template_repo.get(template.id) is not None
        assert template_repo.get(uuid.uuid4()) is None

    def test_create_from_zip_bytes(
        self, template_repo_with_storage_validator: base_repo.TemplateRepository
    ):
        template_repo = template_repo_with_storage_validator
        with open("tests/static/template_valid.zip", "rb") as f:
            zip_bytes = f.read()

        zip_bytesio = io.BytesIO(zip_bytes)

        template = template_repo.create_from_zip_bytes(zip_bytesio)
        template_path = pathlib.Path(str(template.id))

        assert template_repo._file_storage.is_dir(template_path)
        assert template_repo.get(template.id) is not None
        assert template_repo.get(uuid.uuid4()) is None

        with pytest.raises(
            errors.DuplicationError,
            match="Template with this uuid already exists",
        ):
            template = template_repo.create_from_zip_bytes(zip_bytesio)

    def test_update(
        self,
        template_repo: base_repo.TemplateRepository,
    ):
        template_path = pathlib.Path("tests/unit/template/template1")
        template = template_repo.create_from_path(template_path)

        new_title = "new_title"
        new_description = "new_description"
        new_labels = ["new_label_1", "new_label_2"]

        template_repo.update(template, new_title)
        assert template.title == new_title

        template_repo.update(template, description=new_description)
        assert template.description == new_description

        template_repo.update(template, labels=new_labels)
        assert template.labels == new_labels

    def test_template_with_versions(
        self, template_repo: base_repo.TemplateRepository
    ):
        template_path = pathlib.Path("tests/unit/template/template1")
        template = template_repo.create_from_path(template_path)

        assert template_repo.get_versions(template) == []
        assert template_repo.get_version(template, "v0.0.1") is None

        version001 = test_factory.get_version("v0.0.1")
        template_repo.add_version(template, version001)

        assert template_repo.get_version(template, "v0.0.1") == version001

        version216 = test_factory.get_version("v2.1.6")
        template_repo.add_version(template, version216)

        version300 = test_factory.get_version("v3.0.0")
        template_repo.add_version(template, version300)

        assert template_repo.get_versions(template) == [
            version300,
            version216,
            version001,
        ]

    def validate_template_version_dir(
        self,
        local_template_repo: base_repo.TemplateRepository,
        version_path: pathlib.Path,
    ):
        version_meta_path = validator.get_meta_path(version_path)
        version_docx_path = validator.get_template_docx_path(version_path)
        version_json_path = validator.get_template_json_path(version_path)

        assert local_template_repo._file_storage.is_dir(version_path)
        assert local_template_repo._file_storage.is_file(version_meta_path)
        assert local_template_repo._file_storage.is_file(version_docx_path)
        assert local_template_repo._file_storage.is_file(version_json_path)

    def test_create_version(self, template_repo: base_repo.TemplateRepository):
        template_path = pathlib.Path("tests/unit/template/template1")
        template = template_repo.create_from_path(template_path)

        create_version_schema = schema.TemplateVersionCreate(
            tag=meta.VersionTag.from_str("v0.0.1"),
            message="new version",
            docx_file=io.BytesIO(b""),
            json_file=io.BytesIO(b""),
        )

        version = template_repo.create_version(template, create_version_schema)

        assert template_repo.get_version(template, "v0.0.1") == version

        version_path = pathlib.Path(str(template.id), "versions", "v0.0.1")
        self.validate_template_version_dir(template_repo, version_path)

    def test_create_version_from_path(
        self, template_repo: base_repo.TemplateRepository
    ):
        template_path = pathlib.Path("tests/unit/template/template1")
        template = template_repo.create_from_path(template_path)

        assert template_repo.get_version(template, "v0.0.1") is None

        template_version_path = pathlib.Path(
            "tests/unit/template/template1/versions/v0.0.1"
        )
        version = template_repo.create_version_from_path(
            template, template_version_path
        )

        assert template_repo.get_version(template, "v0.0.1") == version

        version_path = pathlib.Path(str(template.id), "versions", "v0.0.1")

        assert template_repo._file_storage.is_dir(version_path)

    def test_create_version_from_zip_bytes(
        self, template_repo_with_storage_validator: base_repo.TemplateRepository
    ):
        template_repo = template_repo_with_storage_validator
        template = test_factory.get_template([])
        with open("tests/static/version_v0.0.1_valid.zip", "rb") as f:
            zip_bytes = f.read()

        zip_bytesio = io.BytesIO(zip_bytes)

        template_version = template_repo.create_version_from_zip_bytes(
            template, zip_bytesio
        )
        assert template_repo.get_version(template, "v0.0.1") == template_version

        template = test_factory.get_template([])
        with open("tests/static/version_v0.0.1_invalid.zip", "rb") as f:
            zip_bytes = f.read()

        zip_bytesio = io.BytesIO(zip_bytes)

        with pytest.raises(errors.TemplateValidationError):
            template_repo.create_version_from_zip_bytes(template, zip_bytesio)

    def test_update_version(
        self,
        template_repo: base_repo.TemplateRepository,
    ):
        template = test_factory.get_template(["v0.0.1"])
        version = test_factory.get_version("v0.0.1")

        new_message = "new template version message"
        assert new_message != version.message

        version = template_repo.update_version(
            template,
            version,
            updates=schema.TemplateVersionUpdate(message=new_message),
        )

        assert version.message == new_message
