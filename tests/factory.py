import uuid

from app.internal.template import entity, meta, version


def get_template_metadata(
    versions: list[str], template_id: uuid.UUID | None = None
):
    return entity.TemplateMetaData(
        versions=[
            meta.VersionTag.from_str(version_str) for version_str in versions
        ],
        title="mock template",
        description="mock description",
        labels=["label"],
        id=template_id or uuid.uuid4(),
    )


def get_template_version_metadata(tag: str):
    return version.TemplateVersionMetaData(
        tag=meta.VersionTag.from_str(tag), message="mocked version"
    )


def get_template(
    versions: list[str], template_id: uuid.UUID | None = None
) -> entity.Template:
    metadata = get_template_metadata(versions, template_id)
    return entity.Template(metadata)


def get_version(tag: str) -> version.TemplateVersion:
    metadata = version.TemplateVersionMetaData(
        tag=meta.VersionTag.from_str(tag), message=f"Version {tag}"
    )
    return version.TemplateVersion(metadata)
