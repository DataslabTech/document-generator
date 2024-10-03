import io
import pathlib
from typing import Any

import pytest

from app.internal import storage
from app.internal.template import entity, validator, version
from tests import factory


@pytest.fixture(scope="module")
def proper_generation_payload() -> dict[str, Any]:
    return {
        "TITLE": "My template title",
        "NUMBER": 2,
        "FLOAT_NUMBER": 3.23,
        "FLOAT_ZERO_NUMBER": 0.0,
        "NESTED_DICT": {
            "NESTED_KEY1": "Nested value",
            "NESTED_KEY2": "Nested value",
            "DEEP_NESTED_KEY": {
                "NUMBER": 24,
                "LIST": [1, 2, 3],
                "LIST_OF_DICTS": [{"KEY1": "value", "KEY2": "value"}],
            },
        },
        "LISTED_VALUE": ["2", "3", "4"],
        "LIST_OF_LISTS": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        "LIST_OF_DICTS": [{"KEY": "value"}, {"KEY": "value"}],
        "NONE": None,
    }


version_meta_yaml = """created_at: '2024-07-01T22:24:41.061069'
message: first version
tag: v1.0.0
updated_at: '2024-07-01T22:24:41.061069'
"""


@pytest.fixture(scope="package")
def version_meta_str() -> str:
    return version_meta_yaml


@pytest.fixture(scope="function")
def version_meta() -> version.TemplateVersionMetaData:
    return version.TemplateVersionMetaData.from_bytes(
        io.BytesIO(version_meta_yaml.encode("utf-8"))
    )


@pytest.fixture(scope="function")
def version_object(
    version_meta: version.TemplateVersionMetaData,
) -> version.TemplateVersion:
    return version.TemplateVersion(version_meta)


@pytest.fixture(scope="session")
def template_meta_yaml() -> str:
    return """created_at: '2024-06-28T14:30:52.773130'
description: Report document description
id: d3a17928-e147-423e-825a-80c987f275a9
labels:
- example
- template
- testing
title: Report document template
updated_at: null
versions:
- v0.0.2
- v0.0.1
"""


template_meta_data_without_versions_yaml = """created_at: '2024-06-28T14:30:52.773130'
description: Report document description
id: d3a17928-e147-423e-825a-80c987f275a9
labels:
- example
- template
- testing
title: Report document template
updated_at: null
versions: []
"""


@pytest.fixture(scope="function")
def template_meta_data(template_meta_yaml: str) -> entity.TemplateMetaData:
    return entity.TemplateMetaData.from_bytes(
        io.BytesIO(template_meta_yaml.encode("utf-8"))
    )


@pytest.fixture(scope="function")
def template_meta_data_without_versions() -> entity.TemplateMetaData:
    return entity.TemplateMetaData.from_bytes(
        io.BytesIO(template_meta_data_without_versions_yaml.encode("utf-8"))
    )


@pytest.fixture(scope="function")
def template(template_meta_data: entity.TemplateMetaData) -> entity.Template:
    tpl = entity.Template(template_meta_data)
    tpl.add_version(factory.get_version("v0.0.1"), update_meta=False)
    tpl.add_version(factory.get_version("v0.0.2"), update_meta=False)
    tpl.add_version(factory.get_version("v0.2.7"))
    tpl.add_version(factory.get_version("v3.0.5"))

    return tpl


@pytest.fixture(scope="function")
def empty_template(
    template_meta_data_without_versions: entity.TemplateMetaData,
) -> entity.Template:
    return entity.Template(template_meta_data_without_versions)


@pytest.fixture(scope="module")
def template_storage() -> storage.Storage:
    return storage.LocalStorage(pathlib.Path("tests/unit/template/templates"))


@pytest.fixture(scope="module")
def tmp_storage(tmp_path: pathlib.Path) -> storage.Storage:
    return storage.LocalStorage(tmp_path)


@pytest.fixture(scope="module")
def template_validator(
    template_storage: storage.Storage,
) -> validator.TemplateValidator:
    return validator.StorageTemplateValidator(template_storage)
