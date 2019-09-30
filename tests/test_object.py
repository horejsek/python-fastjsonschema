import pytest

import fastjsonschema
from fastjsonschema import JsonSchemaDefinitionException, JsonSchemaException


exc = JsonSchemaException('data must be object')
@pytest.mark.parametrize('value, expected', [
    (0, exc),
    (None, exc),
    (True, exc),
    (False, exc),
    ('abc', exc),
    ([], exc),
    ({}, {}),
    ({'x': 1, 'y': True}, {'x': 1, 'y': True}),
])
def test_object(asserter, value, expected):
    asserter({'type': 'object'}, value, expected)


@pytest.mark.parametrize('value, expected', [
    ({}, {}),
    ({'a': 1}, {'a': 1}),
    ({'a': 1, 'b': 2}, JsonSchemaException('data must contain less than or equal to 1 properties')),
])
def test_max_properties(asserter, value, expected):
    asserter({
        'type': 'object',
        'maxProperties': 1,
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ({}, JsonSchemaException('data must contain at least 1 properties')),
    ({'a': 1}, {'a': 1}),
    ({'a': 1, 'b': 2}, {'a': 1, 'b': 2}),
])
def test_min_properties(asserter, value, expected):
    asserter({
        'type': 'object',
        'minProperties': 1,
    }, value, expected)


exc_ab = JsonSchemaException('data must contain [\'a\', \'b\'] properties')
exc_b = JsonSchemaException('data must contain [\'b\'] properties')
@pytest.mark.parametrize('value, expected', [
    ({}, exc_ab),
    ({'a': 1}, exc_b),
    ({'a': 1, 'b': 2}, {'a': 1, 'b': 2}),
])
def test_required(asserter, value, expected):
    asserter({
        'type': 'object',
        'required': ['a', 'b'],
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ({}, {}),
    ({'a': 1}, {'a': 1}),
    ({'a': 1, 'b': ''}, {'a': 1, 'b': ''}),
    ({'a': 1, 'b': 2}, JsonSchemaException('data.b must be string')),
    ({'a': 1, 'b': '', 'any': True}, {'a': 1, 'b': '', 'any': True}),
])
def test_properties(asserter, value, expected):
    asserter({
        'type': 'object',
        'properties': {
            'a': {'type': 'number'},
            'b': {'type': 'string'},
        },
    }, value, expected)


def test_invalid_properties(asserter):
    with pytest.raises(JsonSchemaDefinitionException):
        fastjsonschema.compile({
            'properties': {
                'item': ['wrong'],
            },
        })


@pytest.mark.parametrize('value, expected', [
    ({}, {}),
    ({'a': 1}, {'a': 1}),
    ({'a': 1, 'b': ''}, {'a': 1, 'b': ''}),
    ({'a': 1, 'b': 2}, JsonSchemaException('data.b must be string')),
    ({'a': 1, 'b': '', 'additional': ''}, {'a': 1, 'b': '', 'additional': ''}),
    ({'a': 1, 'b': '', 'any': True}, JsonSchemaException('data.any must be string')),
])
def test_properties_with_additional_properties(asserter, value, expected):
    asserter({
        'type': 'object',
        'properties': {
            'a': {'type': 'number'},
            'b': {'type': 'string'},
        },
        'additionalProperties': {'type': 'string'},
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ({}, {}),
    ({'a': 1}, {'a': 1}),
    ({'a': 1, 'b': ''}, {'a': 1, 'b': ''}),
    ({'a': 1, 'b': 2}, JsonSchemaException('data.b must be string')),
    ({'a': 1, 'b': '', 'any': True}, JsonSchemaException('data must contain only specified properties')),
    ({'cd': True}, JsonSchemaException('data must contain only specified properties')),
    ({'c_d': True}, {'c_d': True}),
])
def test_properties_without_additional_properties(asserter, value, expected):
    asserter({
        'type': 'object',
        'properties': {
            'a': {'type': 'number'},
            'b': {'type': 'string'},
            'c_d': {'type': 'boolean'},
        },
        'additionalProperties': False,
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ({}, {}),
    ({'a': 1}, {'a': 1}),
    ({'xa': 1}, {'xa': 1}),
    ({'xa': ''}, JsonSchemaException('data.xa must be number')),
    ({'xbx': ''}, {'xbx': ''}),
])
def test_pattern_properties(asserter, value, expected):
    asserter({
        'type': 'object',
        'patternProperties': {
            'a': {'type': 'number'},
            'b': {'type': 'string'},
        },
        'additionalProperties': False,
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ({}, {}),
    ({'a': 1}, {'a': 1}),
    ({'b': True}, {'b': True}),
    ({'c': ''}, {'c': ''}),
    ({'d': 1}, JsonSchemaException('data.d must be string')),
])
def test_additional_properties(asserter, value, expected):
    asserter({
        'type': 'object',
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "boolean"},
        },
        "additionalProperties": {"type": "string"}
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ({'id': 1}, {'id': 1}),
    ({'id': 'a'}, JsonSchemaException('data.id must be integer')),
])
def test_object_with_id_property(asserter, value, expected):
    asserter({
        "type": "object",
        "properties": {
            "id": {"type": "integer"}
        }
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ({'$ref': 'ref://to.somewhere'}, {'$ref': 'ref://to.somewhere'}),
    ({'$ref': 1}, JsonSchemaException('data.$ref must be string')),
])
def test_object_with_ref_property(asserter, value, expected):
    asserter({
        "type": "object",
        "properties": {
            "$ref": {"type": "string"}
        }
    }, value, expected)
