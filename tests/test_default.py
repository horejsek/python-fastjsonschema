import math

import pytest

from fastjsonschema import JsonSchemaValueException, validate


@pytest.mark.parametrize('value, expected', [
    (None, JsonSchemaValueException('data must be object', value='{data}', name='data', definition='{definition}', rule='type')),
    ({}, {'a': '', 'b': 42, 'c': {}, 'd': []}),
    ({'a': 'abc'}, {'a': 'abc', 'b': 42, 'c': {}, 'd': []}),
    ({'b': 123}, {'a': '', 'b': 123, 'c': {}, 'd': []}),
    ({'a': 'abc', 'b': 123}, {'a': 'abc', 'b': 123, 'c': {}, 'd': []}),
])
def test_default_in_object(asserter, value, expected):
    asserter({
        'type': 'object',
        'properties': {
            'a': {'type': 'string', 'default': ''},
            'b': {'type': 'number', 'default': 42},
            'c': {'type': 'object', 'default': {}},
            'd': {'type': 'array', 'default': []},
        },
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    (None, JsonSchemaValueException('data must be array', value='{data}', name='data', definition='{definition}', rule='type')),
    ([], ['', 42]),
    (['abc'], ['abc', 42]),
    (['abc', 123], ['abc', 123]),
])
def test_default_in_array(asserter, value, expected):
    asserter({
        'type': 'array',
        'items': [
            {'type': 'string', 'default': ''},
            {'type': 'number', 'default': 42},
        ],
    }, value, expected)


def test_default_turned_off():
    output = validate({
        'type': 'object',
        'properties': {
            'a': {'type': 'string', 'default': ''},
        },
    }, {}, use_default=False)
    assert output == {}


def test_default_non_finite_float():
    """Non-finite float defaults must be generated as valid Python source (#101)."""
    output = validate({
        'type': 'object',
        'properties': {
            'a': {'type': 'number', 'default': float('nan')},
            'b': {'type': 'number', 'default': float('inf')},
            'c': {'type': 'number', 'default': float('-inf')},
        },
    }, {})
    assert math.isnan(output['a'])
    assert output['b'] == float('inf')
    assert output['c'] == float('-inf')


def test_default_non_finite_float_in_array():
    output = validate({
        'type': 'array',
        'items': [{'type': 'number', 'default': float('nan')}],
    }, [])
    assert len(output) == 1 and math.isnan(output[0])


def test_default_nested_non_finite_float():
    output = validate({
        'type': 'object',
        'properties': {
            'a': {'default': {'x': float('inf'), 'y': [1, float('nan')]}},
        },
    }, {})
    assert output['a']['x'] == float('inf')
    assert math.isnan(output['a']['y'][1])
