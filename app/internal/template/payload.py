"""
Payload module for validating user input data for document generation.
"""

from typing import Any

import pydantic


class ValidationResult(pydantic.BaseModel):
    """
    Represents the result of a payload validation.

    Attributes:
        missing_keys: A list of keys expected in the payload but missing.
        extra_keys: A list of keys present in the payload but not expected.
        type_mismatches: A list of keys where the data type does not match the expected type.
    """

    missing_keys: list[str] = []
    extra_keys: list[str] = []
    type_mismatches: list[str] = []

    @property
    def valid(self) -> bool:
        """
        Checks if the payload is valid.

        A payload is considered valid if there are no missing keys, no extra keys,
        and no type mismatches.

        Returns:
            bool: True if the payload is valid, False otherwise.
        """
        return (
            len(self.missing_keys) == 0
            and len(self.extra_keys) == 0
            and len(self.type_mismatches) == 0
        )


def validate(
    proper_dict: dict[str, Any], incoming_dict: dict[str, Any]
) -> ValidationResult:
    """
    Validates an incoming dictionary against a reference dictionary structure.

    Compares the structure of the `incoming_dict` to `proper_dict` and returns a
    `ValidationResult` object that details any differences in terms of missing keys,
    extra keys, or type mismatches.

    Args:
        proper_dict (dict[str, Any]): The reference dictionary with the correct structure.
        incoming_dict (dict[str, Any]): The dictionary to be validated.

    Returns:
        ValidationResult: A report on the validation, detailing any discrepancies.
    """
    return _compare_dicts(proper_dict, incoming_dict, parent_key="")


def _compare_dicts(
    proper_dict: dict[str, Any],
    incoming_dict: dict[str, Any],
    parent_key: str = "",
) -> ValidationResult:
    result = ValidationResult()
    _process_proper_keys(proper_dict, incoming_dict, result, parent_key)
    _process_incoming_keys(proper_dict, incoming_dict, result, parent_key)
    return result


def _process_value(
    proper_value: Any,
    incoming_value: Any,
    result: ValidationResult,
    full_key: str,
):
    if not isinstance(incoming_value, type(proper_value)):
        if not (
            isinstance(proper_value, (int, float))
            and isinstance(incoming_value, (int, float))
        ):
            result.type_mismatches.append(
                f"{full_key} (expected {type(proper_value).__name__}, "
                f"got {type(incoming_value).__name__})"
            )

    elif isinstance(proper_value, dict) and isinstance(incoming_value, dict):
        proper_dict_value: dict[str, Any] = proper_value
        incoming_dict_value: dict[str, Any] = incoming_value
        _compare_nested_dict_values(
            proper_dict_value, incoming_dict_value, result, full_key
        )

    elif isinstance(proper_value, list) and isinstance(incoming_value, list):
        proper_listed_value: list[Any] = proper_value
        incoming_listed_value: list[Any] = incoming_value
        _compare_listed_values(
            proper_listed_value, incoming_listed_value, result, full_key
        )


def _compare_nested_dict_values(
    proper_dict_value: dict[str, Any],
    incoming_dict_value: dict[str, Any],
    result: ValidationResult,
    full_key: str,
) -> None:
    nested_result = _compare_dicts(
        proper_dict_value, incoming_dict_value, full_key
    )
    result.missing_keys.extend(nested_result.missing_keys)
    result.extra_keys.extend(nested_result.extra_keys)
    result.type_mismatches.extend(nested_result.type_mismatches)


def _compare_listed_values(
    proper_listed_value: list[Any],
    incoming_listed_value: list[Any],
    result: ValidationResult,
    full_key: str,
) -> None:
    if len(proper_listed_value) == 0:
        return

    for index, incoming_value in enumerate(incoming_listed_value):
        full_list_key = f"{full_key}[{index}]"
        proper_value: Any = proper_listed_value[0]
        _process_value(proper_value, incoming_value, result, full_list_key)


def _process_proper_keys(
    proper_dict: dict[str, Any],
    incoming_dict: dict[str, Any],
    result: ValidationResult,
    parent_key: str = "",
) -> None:
    for key in proper_dict:
        full_key = f"{parent_key}.{key}" if parent_key else key

        if key not in incoming_dict:
            result.missing_keys.append(full_key)
            continue

        proper_value: Any = proper_dict[key]
        incoming_value: Any = incoming_dict[key]

        _process_value(proper_value, incoming_value, result, full_key)


def _process_incoming_keys(
    proper_dict: dict[str, Any],
    incoming_dict: dict[str, Any],
    result: ValidationResult,
    parent_key: str = "",
) -> None:
    for key in incoming_dict:
        full_key = f"{parent_key}.{key}" if parent_key else key
        if key in proper_dict:
            continue

        result.extra_keys.append(full_key)
