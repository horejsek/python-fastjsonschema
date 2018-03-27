
import pytest

from fastjsonschema import JsonSchemaException


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


exc = JsonSchemaException('data must contain [\'a\', \'b\'] properties')
@pytest.mark.parametrize('value, expected', [
    ({}, exc),
    ({'a': 1}, exc),
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
])
def test_properties_without_additional_properties(asserter, value, expected):
    asserter({
        'type': 'object',
        'properties': {
            'a': {'type': 'number'},
            'b': {'type': 'string'},
        },
        'additionalProperties': False,
    }, value, expected)


@pytest.mark.xfail
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
