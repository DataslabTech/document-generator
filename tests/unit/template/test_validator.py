import io
import pathlib
import unittest
import unittest.mock

import pytest

from app.internal.template import entity, errors, validator, version


@pytest.fixture
def template_validator(mocker: unittest.mock.Mock):
    mock_storage = mocker.Mock()
    return validator.StorageTemplateValidator(validator_storage=mock_storage)


@pytest.mark.parametrize(
    "version_path,is_file_responses,version_meta_yaml_str,valid,error_text",
    [
        (
            "/path/to/version/v1.0.0",
            [True, True, True],
            """created_at: '2024-07-01T22:24:41.061069'
message: first version
tag: v1.0.0
updated_at: '2024-07-01T22:24:41.061069'
""",
            True,
            "",
        ),
        (
            "/path/to/version/some_v.0.1",
            [True, True, True],
            """created_at: '2024-07-01T22:24:41.061069'
message: first version
tag: v1.0.0
updated_at: '2024-07-01T22:24:41.061069'
""",
            False,
            "Version directory name is not a valid version",
        ),
        (
            "/path/to/version/v1.0.0",
            [False, True, True],
            """created_at: '2024-07-01T22:24:41.061069'
message: first version
tag: v1.0.0
updated_at: '2024-07-01T22:24:41.061069'
""",
            False,
            "meta.yaml not found",
        ),
        (
            "/path/to/version/v1.0.0",
            [True, True, True],
            "not valid yaml",
            False,
            "meta.yaml for template version is not valid",
        ),
        (
            "/path/to/version/v1.0.0",
            [True, True, True],
            """created_at: '2024-07-01T22:24:41.061069'
message: first version
tag: v2.0.0
updated_at: '2024-07-01T22:24:41.061069'
""",
            False,
            "Template version tag in directory and in meta.yaml do not match",
        ),
        (
            "/path/to/version/v1.0.0",
            [True, False, True],
            """created_at: '2024-07-01T22:24:41.061069'
message: first version
tag: v1.0.0
updated_at: '2024-07-01T22:24:41.061069'
""",
            False,
            "template.docx not found",
        ),
        (
            "/path/to/version/v1.0.0",
            [True, True, False],
            """created_at: '2024-07-01T22:24:41.061069'
message: first version
tag: v1.0.0
updated_at: '2024-07-01T22:24:41.061069'
""",
            False,
            "template.json not found",
        ),
    ],
)
def test_validate_template_version_dir(
    template_validator: validator.StorageTemplateValidator,
    version_path: str,
    is_file_responses: list[bool],
    version_meta_yaml_str: str,
    valid: bool,
    error_text: str,
):
    valid_path = pathlib.Path(version_path)
    template_validator._storage.is_file.side_effect = is_file_responses
    template_validator._storage.load_file.return_value = io.BytesIO(
        version_meta_yaml_str.encode("utf-8")
    )
    if valid:
        meta = template_validator.validate_version_dir(valid_path)
        assert isinstance(meta, version.TemplateVersionMetaData)
    else:
        with pytest.raises(errors.TemplateValidationError, match=error_text):
            template_validator.validate_version_dir(valid_path)


@pytest.mark.parametrize(
    "template_path,is_dir_responses,is_meta_yaml_file,template_meta_yaml,valid,error_text",
    [
        (
            "/path/to/template/d3a17928-e147-423e-825a-80c987f275a9",
            (True, True),
            True,
            """created_at: '2024-06-28T14:30:52.773130'
description: Report document description
id: d3a17928-e147-423e-825a-80c987f275a9
labels:
- example
- template
- testing
title: Report document template
updated_at: null
versions: []
""",
            True,
            "",
        ),
        (
            "/path/to/template/d3a17928-e147-423e-825a-80c987f275a9",
            (False, True),
            True,
            """created_at: '2024-06-28T14:30:52.773130'
description: Report document description
id: d3a17928-e147-423e-825a-80c987f275a9
labels:
- example
- template
- testing
title: Report document template
updated_at: null
versions: []
""",
            False,
            "Template directory not found",
        ),
        (
            "/path/to/template/d3a17928-e147-423e-825a-80c987f275a9",
            (True, True),
            False,
            """created_at: '2024-06-28T14:30:52.773130'
description: Report document description
id: d3a17928-e147-423e-825a-80c987f275a9
labels:
- example
- template
- testing
title: Report document template
updated_at: null
versions: []
""",
            False,
            "meta.yaml not found",
        ),
        (
            "/path/to/template/d3a17928-e147-423e-825a-80c987f275a9",
            (True, True),
            True,
            "not valid yaml file",
            False,
            "meta.yaml for template is not valid",
        ),
        (
            "/path/to/template/d3a17928-e147-423e-825a-80c987f275a9",
            (True, False),
            True,
            """created_at: '2024-06-28T14:30:52.773130'
description: Report document description
id: d3a17928-e147-423e-825a-80c987f275a9
labels:
- example
- template
- testing
title: Report document template
updated_at: null
versions: []
""",
            False,
            "Versions directory not found",
        ),
    ],
)
def test_validate_template_dir_without_versions(
    template_validator: validator.StorageTemplateValidator,
    template_path: str,
    is_dir_responses: tuple[bool, bool],
    is_meta_yaml_file: bool,
    template_meta_yaml: str,
    valid: bool,
    error_text: str,
):
    valid_path = pathlib.Path(template_path)
    template_validator._storage.is_dir.side_effect = is_dir_responses
    template_validator._storage.is_file.return_value = is_meta_yaml_file
    template_validator._storage.load_file.return_value = io.BytesIO(
        template_meta_yaml.encode("utf-8")
    )
    template_validator._storage.listdir.return_value = []

    if valid:
        meta = template_validator.validate_template_dir(valid_path)
        assert isinstance(meta, entity.TemplateMetaData)
    else:
        with pytest.raises(errors.TemplateValidationError, match=error_text):
            template_validator.validate_template_dir(valid_path)


@pytest.mark.parametrize(
    "template_path,template_meta_yaml,list_dir_responses,valid,error_text",
    [
        (
            "/path/to/template/d3a17928-e147-423e-825a-80c987f275a9",
            """created_at: '2024-06-28T14:30:52.773130'
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
""",
            [pathlib.Path("v0.0.1"), pathlib.Path("v0.0.2")],
            True,
            "",
        ),
        (
            "/path/to/template/d3a17928-e147-423e-825a-80c987f275a9",
            """created_at: '2024-06-28T14:30:52.773130'
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
""",
            [pathlib.Path("v0.0.1")],
            False,
            "Versions in meta.yaml and in versions directory do not match",
        ),
        (
            "/path/to/template/d3a17928-e147-423e-825a-80c987f275a9",
            """created_at: '2024-06-28T14:30:52.773130'
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
""",
            [pathlib.Path("v0.0.1"), pathlib.Path("v0.0.2")],
            False,
            "Versions in meta.yaml and in versions directory do not match",
        ),
    ],
)
def test_validate_template_dir_with_versions(
    template_validator: validator.StorageTemplateValidator,
    mocker: unittest.mock.Mock,
    template_path: str,
    template_meta_yaml: str,
    list_dir_responses: list[pathlib.Path],
    valid: bool,
    error_text: str,
):
    valid_path = pathlib.Path(template_path)
    template_validator._storage.is_dir.side_effect = [True, True]
    template_validator._storage.is_file.return_value = True
    template_validator._storage.load_file.return_value = io.BytesIO(
        template_meta_yaml.encode("utf-8")
    )
    template_validator._storage.listdir.side_effect = [
        list_dir_responses,
        list_dir_responses,
    ]

    # Skipping versions validation because it's already tested in test_validate_template_version_dir
    mocker.patch.object(
        template_validator, "_validate_versions", return_value=None
    )
    if valid:
        meta = template_validator.validate_template_dir(valid_path)
        assert isinstance(meta, entity.TemplateMetaData)
    else:
        with pytest.raises(errors.TemplateValidationError, match=error_text):
            template_validator.validate_template_dir(valid_path)
