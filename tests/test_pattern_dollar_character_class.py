import pytest

from fastjsonschema import JsonSchemaValueException
from fastjsonschema import compile as compile_schema


@pytest.mark.parametrize("pattern, valid, invalid", [
    ("[$]", "$", "a"),
    ("[^$]", "a", "$"),
    ("[a$]", "a", "b"),
    (r"[\$]", "$", "a"),
    (r"\\$", "\\", "$"),
    ("[]]", "]", "a"),
])
def test_pattern_dollar_in_character_class(pattern, valid, invalid):
    validate = compile_schema({
        "type": "string",
        "pattern": pattern,
    })

    assert validate(valid) == valid
    with pytest.raises(JsonSchemaValueException):
        validate(invalid)


@pytest.mark.parametrize("pattern, valid, invalid", [
    (r"\\$", "\\", "\\\n"),
    (r"\\\\$", "\\\\", "\\\\\n"),
])
def test_pattern_dollar_after_even_backslashes(pattern, valid, invalid):
    validate = compile_schema({
        "type": "string",
        "pattern": pattern,
    })

    assert validate(valid) == valid
    with pytest.raises(JsonSchemaValueException):
        validate(invalid)


def test_pattern_properties_dollar_in_character_class():
    validate = compile_schema({
        "type": "object",
        "patternProperties": {
            "[$]": {"type": "integer"},
        },
    })

    assert validate({"$": 1}) == {"$": 1}
    with pytest.raises(JsonSchemaValueException):
        validate({"$": "not an integer"})


def test_pattern_properties_dollar_after_even_backslashes():
    validate = compile_schema({
        "type": "object",
        "patternProperties": {
            r"\\$": {"type": "integer"},
        },
        "additionalProperties": False,
    })

    assert validate({"\\": 1}) == {"\\": 1}
    with pytest.raises(JsonSchemaValueException):
        validate({"\\\n": 1})


def test_property_names_dollar_in_character_class():
    validate = compile_schema({
        "type": "object",
        "propertyNames": {
            "pattern": "[$]",
        },
    })

    assert validate({"$": 1}) == {"$": 1}
    with pytest.raises(JsonSchemaValueException):
        validate({"a": 1})
