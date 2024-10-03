from typing import Any

import pytest

from app.internal.template import payload

valid_payload = {
    "TITLE": "Some title",
    "NUMBER": 242,
    "FLOAT_NUMBER": 4.345,
    "FLOAT_ZERO_NUMBER": 0.0,
    "NESTED_DICT": {
        "NESTED_KEY1": "Some value",
        "NESTED_KEY2": "Nested value",
        "DEEP_NESTED_KEY": {
            "NUMBER": 2424,
            "LIST": [4, 5, 6],
            "LIST_OF_DICTS": [{"KEY1": "value", "KEY2": "value"}],
        },
    },
    "LISTED_VALUE": ["2", "3", "4"],
    "LIST_OF_LISTS": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
    "LIST_OF_DICTS": [{"KEY": "value"}, {"KEY": "value"}],
    "NONE": None,
}


invalid_payload_top_level = {
    "ANOTHER_TITLE": "Another title",
    "NUMBER": "242",
    "FLOAT_NUMBER": 4.345,
    "FLOAT_ZERO_NUMBER": 0,
    "NESTED_DICT": {
        "NESTED_KEY1": "Some value",
        "NESTED_KEY2": "Nested value",
        "DEEP_NESTED_KEY": {
            "NUMBER": 2424,
            "LIST": [4, 5, 6],
            "LIST_OF_DICTS": [{"KEY1": "value", "KEY2": "value"}],
        },
    },
    "LISTED_VALUE": ["2", "3", "4"],
    "LIST_OF_LISTS": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
    "LIST_OF_DICTS": [{"KEY": "value"}, {"KEY": "value"}],
    "NONE": None,
}

invalid_payload_nested_keys = {
    "TITLE": "Some title",
    "NUMBER": 242,
    "FLOAT_NUMBER": 4.345,
    "FLOAT_ZERO_NUMBER": 0.0,
    "NESTED_DICT": {
        "NESTED_KEY2": 1111,
        "NESTED_KEY3": "redundant",
        "DEEP_NESTED_KEY": {
            "NUMBER": "2424",
            "REDUNDANT_KEY": "value",
            "LIST": ["4", "5", "6"],
            "LIST_OF_DICTS": [{"KEY1": "value", "KEY3": "value"}],
        },
    },
    "LISTED_VALUE": ["2", "3", "4"],
    "LIST_OF_LISTS": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
    "LIST_OF_DICTS": [{"KEY": "value"}, {"KEY": "value"}],
    "NONE": None,
}

invalid_payload_listed_keys = {
    "TITLE": "Some title",
    "NUMBER": 242,
    "FLOAT_NUMBER": 4.345,
    "FLOAT_ZERO_NUMBER": 0.0,
    "NESTED_DICT": {
        "NESTED_KEY1": "Some value",
        "NESTED_KEY2": "Nested value",
        "DEEP_NESTED_KEY": {
            "NUMBER": 2424,
            "LIST": [4, 5, 6],
            "LIST_OF_DICTS": [{"KEY1": "value", "KEY2": "value"}],
        },
    },
    "LISTED_VALUE": [2, "3", 4],
    "LIST_OF_LISTS": [
        [1, None, 3],
        [4, 5, ("A", "B")],
        [{"SOME_KEY": "some_value"}, 8, 9],
    ],
    "LIST_OF_DICTS": [
        {"ANOTHER_KEY": "value"},
        {"KEY": 0, "KEY2": "value2"},
    ],
    "NONE": None,
}


@pytest.mark.parametrize(
    "incoming_dict,missing_keys,extra_keys,type_mismatches,valid",
    [
        (
            valid_payload,
            [],
            [],
            [],
            True,
        ),
        (
            invalid_payload_top_level,
            ["TITLE"],
            ["ANOTHER_TITLE"],
            ["NUMBER (expected int, got str)"],
            False,
        ),
        (
            invalid_payload_nested_keys,
            [
                "NESTED_DICT.NESTED_KEY1",
                "NESTED_DICT.DEEP_NESTED_KEY.LIST_OF_DICTS[0].KEY2",
            ],
            [
                "NESTED_DICT.DEEP_NESTED_KEY.LIST_OF_DICTS[0].KEY3",
                "NESTED_DICT.DEEP_NESTED_KEY.REDUNDANT_KEY",
                "NESTED_DICT.NESTED_KEY3",
            ],
            [
                "NESTED_DICT.NESTED_KEY2 (expected str, got int)",
                "NESTED_DICT.DEEP_NESTED_KEY.NUMBER (expected int, got str)",
                "NESTED_DICT.DEEP_NESTED_KEY.LIST[0] (expected int, got str)",
                "NESTED_DICT.DEEP_NESTED_KEY.LIST[1] (expected int, got str)",
                "NESTED_DICT.DEEP_NESTED_KEY.LIST[2] (expected int, got str)",
            ],
            False,
        ),
        (
            invalid_payload_listed_keys,
            ["LIST_OF_DICTS[0].KEY"],
            ["LIST_OF_DICTS[0].ANOTHER_KEY", "LIST_OF_DICTS[1].KEY2"],
            [
                "LISTED_VALUE[0] (expected str, got int)",
                "LISTED_VALUE[2] (expected str, got int)",
                "LIST_OF_LISTS[0][1] (expected int, got NoneType)",
                "LIST_OF_LISTS[1][2] (expected int, got tuple)",
                "LIST_OF_LISTS[2][0] (expected int, got dict)",
                "LIST_OF_DICTS[1].KEY (expected str, got int)",
            ],
            False,
        ),
    ],
)
@pytest.mark.usefixtures("proper_generation_payload")
def test_validate_payload(
    proper_generation_payload: dict[str, Any],
    incoming_dict: dict[str, Any],
    missing_keys: list[str],
    extra_keys: list[str],
    type_mismatches: list[str],
    valid: bool,
) -> None:
    result = payload.validate(proper_generation_payload, incoming_dict)
    assert result.missing_keys == missing_keys
    assert result.extra_keys == extra_keys
    assert result.type_mismatches == type_mismatches
    assert result.valid == valid
