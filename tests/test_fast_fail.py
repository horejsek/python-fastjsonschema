import pytest

from fastjsonschema import (
    JsonSchemaValueException,
    JsonSchemaValuesException,
    compile,
    compile_to_code,
)


def test_fast_fail():
    validator = compile({
        'type': 'object',
        'properties': {
            'string': {
                'type': 'string',
            },
            'number': {
                'type': 'number',
            },
        },
    })

    with pytest.raises(JsonSchemaValueException) as exc_info:
        validator({
            'string': 1,
            'number': 'a',
        })
    assert exc_info.value.message == 'data.string must be string'


def test_captures_all_errors():
    validator = compile({
        'type': 'object',
        'properties': {
            'string': {
                'type': 'string',
            },
            'number': {
                'type': 'number',
            },
        },
    }, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc_info:
        validator({
            'string': 1,
            'number': 'a',
        })
    assert len(exc_info.value.errors) == 2
    assert exc_info.value.errors[0].message == 'data.string must be string'
    assert exc_info.value.errors[1].message == 'data.number must be number'


INT_OR_STRING = {
    'definitions': {'int': {'type': 'integer'}},
    'anyOf': [{'$ref': '#/definitions/int'}, {'type': 'string'}],
}
IF_THEN_ELSE = {'if': {'type': 'integer'}, 'then': {'minimum': 10}, 'else': {'type': 'string'}}


# anyOf, oneOf, not, if, contains and propertyNames only try their subschemas out and catch
# the failure, so they used to be decided by an exception that fast_fail=False never raises.
@pytest.mark.parametrize('definition, value, is_valid', [
    ({'anyOf': [{'type': 'integer'}, {'type': 'string'}]}, 'abc', True),
    ({'anyOf': [{'type': 'integer'}, {'type': 'string'}]}, 1.5, False),
    ({'oneOf': [{'type': 'integer'}, {'minimum': 2}]}, 1, True),
    ({'oneOf': [{'type': 'integer'}, {'minimum': 2}]}, 2.5, True),
    ({'oneOf': [{'type': 'integer'}, {'minimum': 2}]}, 3, False),
    ({'not': {'type': 'integer'}}, 'abc', True),
    ({'not': {'type': 'integer'}}, 1, False),
    (IF_THEN_ELSE, 'abc', True),
    (IF_THEN_ELSE, 42, True),
    (IF_THEN_ELSE, 1, False),
    (IF_THEN_ELSE, 1.5, False),
    ({'contains': {'type': 'number'}}, ['abc', 1], True),
    ({'contains': {'type': 'number'}}, ['abc'], False),
    ({'propertyNames': {'maxLength': 3}}, {'foo': 1}, True),
    ({'propertyNames': {'maxLength': 3}}, {'foobar': 1}, False),
    # Nested, so an inner attempt must not decide the outer one.
    ({'anyOf': [{'oneOf': [{'type': 'integer'}]}, {'type': 'string'}]}, 'abc', True),
    ({'not': {'anyOf': [{'type': 'integer'}, {'type': 'string'}]}}, 1.5, True),
    ({'not': {'anyOf': [{'type': 'integer'}, {'type': 'string'}]}}, 'abc', False),
    # A subschema behind $ref becomes its own function reporting through JsonSchemaValuesException.
    (INT_OR_STRING, 'abc', True),
    (INT_OR_STRING, 42, True),
    (INT_OR_STRING, 1.5, False),
    (dict(IF_THEN_ELSE, **{'definitions': {'int': {'type': 'integer'}}, 'if': {'$ref': '#/definitions/int'}}), 'abc', True),
    ({'definitions': {'int': {'type': 'integer'}}, 'not': {'$ref': '#/definitions/int'}}, 'abc', True),
    ({'definitions': {'int': {'type': 'integer'}}, 'not': {'$ref': '#/definitions/int'}}, 1, False),
    ({'definitions': {'num': {'type': 'number'}}, 'contains': {'$ref': '#/definitions/num'}}, ['abc', 1], True),
])
def test_fast_fail_does_not_change_the_verdict(definition, value, is_valid):
    for fast_fail in (True, False):
        validator = compile(dict(definition), fast_fail=fast_fail)
        if is_valid:
            assert validator(value) == value
        else:
            with pytest.raises((JsonSchemaValueException, JsonSchemaValuesException)):
                validator(value)


def test_rejected_attempt_does_not_leak_its_errors():
    validator = compile({
        'type': 'object',
        'properties': {
            'value': {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            'number': {'type': 'number'},
        },
    }, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc_info:
        validator({'value': 'abc', 'number': 'a'})
    assert [error.message for error in exc_info.value.errors] == ['data.number must be number']


def test_failing_composition_reports_its_own_error():
    validator = compile({
        'type': 'object',
        'properties': {
            'value': {'anyOf': [{'type': 'integer'}, {'type': 'string'}]},
            'number': {'type': 'number'},
        },
    }, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc_info:
        validator({'value': 1.5, 'number': 'a'})
    assert [error.message for error in exc_info.value.errors] == [
        'data.value cannot be validated by any definition',
        'data.number must be number',
    ]


def test_captures_errors_behind_ref():
    validator = compile({
        'type': 'object',
        'definitions': {'int': {'type': 'integer'}},
        'properties': {
            'a': {'$ref': '#/definitions/int'},
            'b': {'type': 'string'},
        },
    }, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc_info:
        validator({'a': 'abc', 'b': 1})
    assert [error.message for error in exc_info.value.errors] == [
        'data.a must be integer',
        'data.b must be string',
    ]


def test_captures_errors_next_to_one_of():
    validator = compile({
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'value': {'oneOf': [{'type': 'string'}, {'type': 'integer'}]},
        },
    }, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc_info:
        validator({'name': 1, 'value': []})
    assert [error.message for error in exc_info.value.errors] == [
        'data.name must be string',
        'data.value must be valid exactly by one definition (0 matches found)',
    ]


def test_captures_errors_next_to_nested_ref():
    validator = compile({
        'definitions': {'age': {'type': 'integer'}},
        'type': 'object',
        'properties': {
            'name': {'type': 'string'},
            'value': {
                'type': 'object',
                'properties': {
                    'age': {'$ref': '#/definitions/age'},
                },
            },
        },
    }, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc_info:
        validator({'name': 1, 'value': {'age': 'old'}})
    assert [error.message for error in exc_info.value.errors] == [
        'data.name must be string',
        'data.value.age must be integer',
    ]


@pytest.mark.parametrize('definition, value, expected', [
    (
        {'items': {'type': 'integer', 'minimum': 5}},
        [1, 'a', 7, 2],
        ['data[0] must be bigger than or equal to 5', 'data[1] must be integer', 'data[3] must be bigger than or equal to 5'],
    ),
    (
        {'items': [{'type': 'integer'}, {'type': 'string'}], 'additionalItems': {'type': 'null'}},
        ['a', 1, 2],
        ['data[0] must be integer', 'data[1] must be string', 'data[2] must be null'],
    ),
    (
        {'patternProperties': {'^i_': {'type': 'integer'}}, 'additionalProperties': {'type': 'string'}},
        {'i_a': 'x', 'i_b': 1, 'c': 2},
        ['data.i_a must be integer', 'data.c must be string'],
    ),
    (
        {'required': ['a', 'b'], 'minProperties': 3, 'properties': {'c': {'type': 'string'}}},
        {'c': 1},
        ['data must contain at least 3 properties', "data must contain ['a', 'b'] properties", 'data.c must be string'],
    ),
    (
        {'dependencies': {'a': {'required': ['b']}, 'c': ['d']}},
        {'a': 1, 'c': 1},
        ["data must contain ['b'] properties", 'data missing dependency d for c'],
    ),
    (
        {'allOf': [{'type': 'integer'}, {'minimum': 5}, {'multipleOf': 2}]},
        3.5,
        ['data must be integer', 'data must be bigger than or equal to 5', 'data must be multiple of 2'],
    ),
    (
        {'if': {'type': 'integer'}, 'then': {'minimum': 5, 'multipleOf': 2}, 'else': {'type': 'string', 'maxLength': 1}},
        3,
        ['data must be bigger than or equal to 5', 'data must be multiple of 2'],
    ),
    (
        {'properties': {'a': {'anyOf': [{'type': 'integer'}]}, 'b': {'not': {'type': 'null'}}, 'c': {'contains': {'type': 'null'}}}},
        {'a': 'x', 'b': None, 'c': [1]},
        ['data.a cannot be validated by any definition', 'data.b must NOT match a disallowed definition', 'data.c must contain one of contains definition'],
    ),
    (
        {'type': 'array', 'maxItems': 1, 'items': {'$ref': '#'}},
        [[1, 2], [[]]],
        ['data must contain less than or equal to 1 items', 'data[0] must contain less than or equal to 1 items', 'data[0][0] must be array', 'data[0][1] must be array'],
    ),
    (
        {'type': 'object', 'propertyNames': False},
        'abc',
        ['data must be object'],
    ),
])
def test_captures_all_nested_errors(definition, value, expected):
    validator = compile(definition, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc_info:
        validator(value)
    assert [error.message for error in exc_info.value.errors] == expected


def test_values_exception_message():
    validator = compile({'properties': {'a': {'type': 'string'}, 'b': {'type': 'integer'}}}, fast_fail=False)

    with pytest.raises(JsonSchemaValuesException) as exc_info:
        validator({'a': 1, 'b': 'x'})
    assert exc_info.value.message == 'data.a must be string; data.b must be integer'
    assert str(exc_info.value) == exc_info.value.message


@pytest.mark.parametrize('value, is_valid', [('abc', True), (42, True), (1.5, False)])
def test_generated_code_verdict(tmp_path, monkeypatch, value, is_valid):
    with open(tmp_path / 'schema_fast_fail.py', 'w') as f:
        f.write(compile_to_code(dict(INT_OR_STRING), fast_fail=False))
    with monkeypatch.context() as m:
        m.syspath_prepend(tmp_path)
        from schema_fast_fail import validate
    if is_valid:
        assert validate(value) == value
    else:
        with pytest.raises(JsonSchemaValuesException):
            validate(value)
