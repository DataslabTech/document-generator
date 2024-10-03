import datetime
import io

from app.internal.template import version


def create_version_metadata_from_str(
    meta_str: str,
) -> version.TemplateVersionMetaData:
    return version.TemplateVersionMetaData.from_bytes(
        io.BytesIO(meta_str.encode("utf-8"))
    )


def test_version_meta_data_bytes_transform(
    version_meta: version.TemplateVersionMetaData, version_meta_str: str
):
    yaml_after = version_meta.to_bytes().getvalue().decode("utf-8")
    assert version_meta_str == yaml_after


class TestVersion:
    def test_init(self, version_meta: version.TemplateVersionMetaData):
        version_object = version.TemplateVersion(version_meta)
        assert version_object.tag == version_meta.tag
        assert version_object.tag_str == version_meta.tag.tag
        assert version_object.message == version_meta.message
        assert version_object.created_at == version_meta.created_at
        assert version_object.updated_at == version_meta.updated_at

    def test_update(self, version_object: version.TemplateVersion):
        new_message = "new_message"
        new_updated_at = datetime.datetime.now()
        version_object.message = new_message
        version_object.updated_at = new_updated_at

        assert version_object.message == new_message
        assert version_object.updated_at == new_updated_at
