import pathlib
import uuid

from app.internal.template import entity, factory, validator, version
from tests import factory as test_factory


class MockTemplateValidator(validator.TemplateValidator):
    def validate_template_dir(
        self, path: pathlib.Path
    ) -> entity.TemplateMetaData:
        return test_factory.get_template_metadata(["v0.0.1", "v0.0.2"])

    def validate_version_dir(
        self, version_path: pathlib.Path
    ) -> version.TemplateVersionMetaData:
        version_tag = version_path.name

        return test_factory.get_template_version_metadata(version_tag)


class MockTemplateFactory(factory.TemplateFactory):
    def create_template_meta(
        self, template_path: pathlib.Path
    ) -> entity.TemplateMetaData:
        template_id = template_path.name
        try:
            template_id = uuid.UUID(template_id)
        except ValueError:
            template_id = None
        return test_factory.get_template_metadata(
            ["v0.0.1", "v0.0.2"], template_id
        )

    def create_template_version_meta(
        self, version_path: pathlib.Path
    ) -> version.TemplateVersionMetaData:
        version_tag = version_path.name
        return test_factory.get_template_version_metadata(version_tag)

    def create_template(self, template_path: pathlib.Path) -> entity.Template:
        template_id = template_path.name
        try:
            template_id = uuid.UUID(template_id)
        except ValueError:
            template_id = None
        return test_factory.get_template([], template_id)

    def create_template_version(
        self, version_path: pathlib.Path
    ) -> version.TemplateVersion:
        version_tag = version_path.name
        return test_factory.get_version(version_tag)
