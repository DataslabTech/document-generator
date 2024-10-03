import io

import pytest

from app.internal.template import meta


@pytest.mark.parametrize(
    "tag,valid,parsed",
    [
        ("v1.0.0", True, (1, 0, 0)),
        ("v234.53.938", True, (234, 53, 938)),
        ("v1,2,3", False, None),
        ("v27", False, None),
        ("v1.0", False, None),
        ("v.2.4.6", False, None),
        ("v 1.2.3", False, None),
        ("v3.2.0 and some extra characters", False, None),
        ("Some extra characters and v1.2.3", False, None),
        ("", False, None),
    ],
)
def test_version_parsing(
    tag: str, valid: bool, parsed: tuple[int, int, int] | None
):
    assert meta.is_version(tag) == valid
    if valid:
        assert meta.parse_version(tag) == parsed
    else:
        with pytest.raises(ValueError):
            meta.parse_version(tag)


class TestVersionTag:
    @pytest.mark.parametrize(
        "tag_str, expected",
        [
            ("v1.2.3", meta.VersionTag(1, 2, 3)),
            ("v12.345.678", meta.VersionTag(12, 345, 678)),
        ],
    )
    def test_from_str(self, tag_str: str, expected: meta.VersionTag):
        assert meta.VersionTag.from_str(tag_str) == expected

    @pytest.mark.parametrize("tag_str", ["v1,2,3", "v27", "v1.0", "invalid"])
    def test_from_str_failure(self, tag_str: str):
        with pytest.raises(ValueError):
            meta.VersionTag.from_str(tag_str)

    def test_tag_property(self):
        tag = meta.VersionTag(1, 2, 3)
        assert tag.tag == "v1.2.3"

    @pytest.mark.parametrize(
        "tag1,tag2,equal",
        [
            (meta.VersionTag(1, 2, 3), meta.VersionTag(1, 2, 3), True),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(3, 2, 1), False),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(3, 2, 3), False),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(1, 2, 4), False),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(1, 3, 1), False),
        ],
    )
    def test_is_equal_to(
        self, tag1: meta.VersionTag, tag2: meta.VersionTag, equal: bool
    ):
        assert tag1.is_equal_to(tag2) == equal

    @pytest.mark.parametrize(
        "tag1, tag2, less_than",
        [
            (meta.VersionTag(1, 2, 3), meta.VersionTag(1, 2, 4), True),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(1, 3, 3), True),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(2, 2, 3), True),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(1, 2, 3), False),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(1, 2, 2), False),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(1, 1, 3), False),
            (meta.VersionTag(1, 2, 3), meta.VersionTag(0, 2, 3), False),
        ],
    )
    def test_less_than(
        self, tag1: meta.VersionTag, tag2: meta.VersionTag, less_than: bool
    ):
        assert tag1.less_than(tag2) == less_than


def test_meta_data_bytes_transform():
    yaml_init = "created_at: '2024-07-01T22:24:41.061069'\nupdated_at: '2024-07-01T22:24:41.061069'\n"

    meta_data = meta.MetaData.from_bytes(io.BytesIO(yaml_init.encode("utf-8")))
    yaml_after = meta_data.to_bytes().getvalue().decode("utf-8")
    assert yaml_init == yaml_after
