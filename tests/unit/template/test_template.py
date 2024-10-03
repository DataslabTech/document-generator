import datetime
import io

import pytest

from app.internal.template import entity, meta, version
from tests import factory

metadata_yaml_str = """created_at: '2024-06-28T14:30:52.773130'
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


class TestTemplateMetaData:

    def test_transform(self):
        metadata = entity.TemplateMetaData.from_bytes(
            io.BytesIO(metadata_yaml_str.encode("utf-8"))
        )
        yaml_after = metadata.to_bytes().getvalue().decode("utf-8")
        assert metadata_yaml_str == yaml_after

    def test_add_version(self, template_meta_data: entity.TemplateMetaData):
        new_major_version = meta.VersionTag(1, 0, 5)
        template_meta_data.add_version(new_major_version)
        assert new_major_version in template_meta_data.versions
        assert new_major_version == template_meta_data.versions[0]

        new_minor_version = meta.VersionTag(0, 3, 0)
        template_meta_data.add_version(new_minor_version)
        assert new_minor_version in template_meta_data.versions
        assert new_minor_version == template_meta_data.versions[1]

        new_patch_version = meta.VersionTag(0, 0, 0)
        template_meta_data.add_version(new_patch_version)
        assert new_patch_version in template_meta_data.versions
        assert new_patch_version == template_meta_data.versions[-1]


class TestTemplate:
    def test_init(self, template_meta_data: entity.TemplateMetaData):
        """
        Тест на перевірку коректності ініціалізації об'єкта Template
        з метаданими TemplateMetaData.

        Args:
          template_meta_data: Метадані шаблону.
        """
        template = entity.Template(template_meta_data)
        assert template.title == template_meta_data.title
        assert template.id == template_meta_data.id
        assert template.description == template_meta_data.description
        assert template.versions == template_meta_data.versions
        assert template.labels == template_meta_data.labels
        assert template.created_at == template_meta_data.created_at
        assert template.updated_at == template_meta_data.updated_at

    def test_update(self, template: entity.Template):
        new_title = "New template title"
        template.title = new_title

        new_description = "New template description"
        template.description = new_description

        new_labels = ["label1", "label2"]
        template.labels = new_labels

        new_updated_at = datetime.datetime.now()
        template.updated_at = new_updated_at

        assert template.title == new_title
        assert template.description == new_description
        assert template.labels == new_labels
        assert template.updated_at == new_updated_at

    def test_get_version(self, template: entity.Template):
        print(template.versions)

        v001 = template.get_version("v0.0.1")
        v002 = template.get_version("v0.0.2")

        assert v001, "version v0.0.1 not found"
        assert v002, "version v0.0.2 not found"

        v003 = template.get_version("v0.0.3")

        assert not v003, "version v0.0.3 found but shouldn't"

        with pytest.raises(ValueError):
            template.get_version("incorrect v1.0.0")

    def check_versions_order(
        self, versions: list[version.TemplateVersion]
    ) -> None:
        print([v.tag for v in versions])
        prev_version: version.TemplateVersion | None = None
        for ver in versions:
            if prev_version is not None:
                assert ver.tag.less_than(
                    prev_version.tag
                ), f"version {ver.tag} must be before {prev_version.tag}"
            prev_version = ver

    def test_get_versions(self, template: entity.Template):
        versions = template.get_versions()
        self.check_versions_order(versions)

        template.add_version(factory.get_version("v4.0.0"))
        template.add_version(factory.get_version("v0.1.0"))

        self.check_versions_order(versions)

    def test_get_latest_version(self, empty_template: entity.Template):
        latest_version = empty_template.get_latest_version()
        assert latest_version is None

        empty_template.add_version(
            factory.get_version("v0.0.1"), update_meta=False
        )
        empty_template.add_version(factory.get_version("v0.2.7"))
        empty_template.add_version(factory.get_version("v3.0.5"))

        latest_version = empty_template.get_latest_version()
        assert latest_version is not None
        assert latest_version.tag.tag == "v3.0.5"

    def test_add_version(self, empty_template: entity.Template):
        new_version = empty_template.get_version("v0.0.1")
        assert new_version is None

        empty_template.add_version(factory.get_version("v0.0.1"))
        new_version = empty_template.get_version("v0.0.1")
        assert new_version is not None
        assert new_version.tag.tag == "v0.0.1"

        with pytest.raises(ValueError):
            empty_template.add_version(factory.get_version("v0.0.1"))
