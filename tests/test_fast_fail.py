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
