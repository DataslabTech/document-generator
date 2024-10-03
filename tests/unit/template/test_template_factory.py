import io
import pathlib
import unittest.mock

import pytest

from app.internal.template import factory
from tests import factory as tests_factory
from tests.mock import template_mock


@pytest.fixture
def template_factory(mocker: unittest.mock.Mock) -> factory.TemplateFactory:
    mock_storage = mocker.Mock()
    return factory.StorageTemplateFactory(
        template_storage=mock_storage,
        template_validator=template_mock.MockTemplateValidator(),
    )


def test_create_template_meta(
    template_factory: factory.TemplateFactory, template_meta_yaml: str
):
    template_factory._storage.load_file.return_value = io.BytesIO(
        template_meta_yaml.encode("utf-8")
    )
    template_meta = template_factory.create_template_meta(
        pathlib.Path("/path/to/template")
    )


def test_create_template_version_meta(
    template_factory: factory.TemplateFactory, version_meta_str: str
):
    template_factory._storage.load_file.return_value = io.BytesIO(
        version_meta_str.encode("utf-8")
    )
    version_meta = template_factory.create_template_version_meta(
        pathlib.Path("/path/to/template/version/v0.0.1")
    )


def test_create_template_version(
    template_factory: factory.TemplateFactory, version_meta_str: str
):
    template_factory._storage.load_file.return_value = io.BytesIO(
        version_meta_str.encode("utf-8")
    )
    tpl_version = template_factory.create_template_version(
        pathlib.Path("/path/to/template/version/v0.0.1")
    )


def test_create_template(
    template_factory: factory.TemplateFactory, template_meta_yaml: str
):
    template_factory._storage.load_file.side_effect = [
        io.BytesIO(template_meta_yaml.encode("utf-8")),
        io.BytesIO(
            """created_at: '2024-07-01T22:24:41.061069'
message: first version
tag: v0.0.1
updated_at: '2024-07-01T22:24:41.061069'""".encode(
                "utf-8"
            )
        ),
        io.BytesIO(
            """created_at: '2024-07-01T22:24:41.061069'
message: first version
tag: v0.0.2
updated_at: '2024-07-01T22:24:41.061069'""".encode(
                "utf-8"
            ),
        ),
    ]
    template_factory._storage.listdir.return_value = (
        pathlib.Path("/path/to/template/versions/v0.0.1"),
        pathlib.Path("/path/to/template/versions/v0.0.2"),
    )
    tpl_version = template_factory.create_template(
        pathlib.Path("/path/to/template/")
    )
