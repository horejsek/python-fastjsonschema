import pytest

import fastjsonschema
from fastjsonschema import JsonSchemaValueException


def _composition_example(composition="oneOf"):
    return {
        "definitions": {
            "multiple-of-3": {"type": "number", "multipleOf": 3},
            "multiple-of-5": {"type": "number", "multipleOf": 5},
        },
        composition: [
            {"$ref": "#/definitions/multiple-of-3"},
            {"$ref": "#/definitions/multiple-of-5"},
        ],
    }


@pytest.mark.parametrize(
    "composition, value",
    [("oneOf", 10), ("allOf", 15), ("anyOf", 9)]
)
def test_composition(asserter, composition, value):
    asserter(_composition_example(composition), value, value)


@pytest.mark.parametrize(
    "composition, value",
    [("oneOf", 2), ("anyOf", 2), ("allOf", 3)]
)
def test_ref_is_expanded_on_composition_error(composition, value):
    with pytest.raises(JsonSchemaValueException) as exc:
        fastjsonschema.validate(_composition_example(composition), value)

    if composition in exc.value.definition:
        assert exc.value.definition[composition] == [
            {"type": "number", "multipleOf": 3},
            {"type": "number", "multipleOf": 5},
        ]
    else:
        # allOf will fail on the first invalid item,
        # so the error message will not refer to the entire composition
        assert composition == "allOf"
        assert "$ref" not in exc.value.definition
        assert exc.value.definition["type"] == "number"


@pytest.mark.parametrize(
    "composition, value",
    [("oneOf", 2), ("anyOf", 2), ("allOf", 3)]
)
def test_ref_is_expanded_with_resolver(composition, value):
    repo = {
        "sch://multiple-of-3": {"type": "number", "multipleOf": 3},
        "sch://multiple-of-5": {"type": "number", "multipleOf": 5},
    }
    schema = {
        composition: [
            {"$ref": "sch://multiple-of-3"},
            {"$ref": "sch://multiple-of-5"},
        ]
    }

    with pytest.raises(JsonSchemaValueException) as exc:
        fastjsonschema.validate(schema, value, handlers={"sch": repo.__getitem__})

    if composition in exc.value.definition:
        assert exc.value.definition[composition] == [
            {"type": "number", "multipleOf": 3},
            {"type": "number", "multipleOf": 5},
        ]
    else:
        # allOf will fail on the first invalid item,
        # so the error message will not refer to the entire composition
        assert composition == "allOf"
        assert "$ref" not in exc.value.definition
        assert exc.value.definition["type"] == "number"
