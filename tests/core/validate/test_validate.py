from core.config import ValidationItem
from core.validate import Validator, ValidationError, ValidatedObject


def test_valid_json_lines(static_file):
    validator = Validator(
        [
            ValidationItem(
                name="test_schema",
                origin="test-origin",
                schema_path=static_file("test_json_schema.json"),
            )
        ]
    )
    objects, errors = validator.get_validated_objects_from_file(
        static_file("lines.jsonl")
    )

    assert len(objects) == 2, objects
    assert len(errors) == 0, errors

    assert objects == [
        ValidatedObject(origin="test-origin", data={"tag": 1, "some_object": {}}),
        ValidatedObject(origin="test-origin", data={"tag": 2, "some_object": {}}),
    ]


def test_invalid_json_lines(static_file):
    validator = Validator(
        [
            ValidationItem(
                name="test_schema",
                origin="test-origin",
                schema_path=static_file("test_json_schema.json"),
            )
        ]
    )
    objects, errors = validator.get_validated_objects_from_file(
        static_file("lines.jsonl")
    )

    assert len(objects) == 0, objects
    assert len(errors) == 2, errors

    assert errors == [
        ValidationError(
            path="",
            line_no=1,
            message="Invalid JSON: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
        ),
        ValidationError(
            path="",
            line_no=2,
            message="Invalid JSON: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
        ),
    ]


def test_invalid_json_lines_with_schema_error(static_file):
    validator = Validator(
        [
            ValidationItem(
                name="test_schema",
                origin="test-origin",
                schema_path=static_file("test_json_schema.json"),
            )
        ]
    )
    objects, errors = validator.get_validated_objects_from_file(
        static_file("lines.jsonl")
    )

    assert len(objects) == 0, objects
    assert len(errors) == 2, errors

    assert errors == [
        ValidationError(
            path="",
            line_no=1,
            message="Additional properties are not allowed ('additional_property' was unexpected)",
        ),
        ValidationError(
            path="",
            line_no=2,
            message="Additional properties are not allowed ('additional_property' was unexpected)",
        ),
    ]


def test_invalid_json_lines_with_partial_object(static_file):
    validator = Validator(
        [
            ValidationItem(
                name="test_schema",
                origin="test-origin",
                schema_path=static_file("test_json_schema.json"),
            )
        ]
    )
    objects, errors = validator.get_validated_objects_from_file(
        static_file("lines.jsonl")
    )

    assert len(objects) == 1, objects
    assert len(errors) == 1, errors

    assert errors == [
        ValidationError(
            path="",
            line_no=1,
            message="Additional properties are not allowed ('additional_property' was unexpected)",
        ),
    ]

    assert objects == [
        ValidatedObject(origin="test-origin", data={"tag": 2, "some_object": {}})
    ]


def test_multi_schema_selects_origin(static_file):
    validator = Validator(
        [
            ValidationItem(
                name="schema_a",
                origin="device-a",
                schema_path=static_file("schema_a.json"),
            ),
            ValidationItem(
                name="schema_b",
                origin="device-b",
                schema_path=static_file("schema_b.json"),
            ),
        ]
    )
    objects, errors = validator.get_validated_objects_from_file(
        static_file("lines.jsonl")
    )

    assert len(errors) == 0, errors
    assert objects == [
        ValidatedObject(origin="device-a", data={"tag": 1, "value": 10}),
        ValidatedObject(origin="device-b", data={"tag": 2, "value": 20}),
    ]
