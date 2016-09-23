
import pytest

from fastjsonschema import JsonSchemaException


@pytest.fixture(params=['number', 'integer'])
def number_type(request):
    return request.param


exc = JsonSchemaException('data must be {number_type}')
@pytest.mark.parametrize('value, expected', [
    (-5, -5),
    (0, 0),
    (5, 5),
    (None, exc),
    (True, exc),
    ('abc', exc),
    ([], exc),
    ({}, exc),
])
def test_number(asserter, number_type, value, expected):
    if isinstance(expected, JsonSchemaException):
        expected = JsonSchemaException(expected.message.format(number_type=number_type))
    asserter({'type': number_type}, value, expected)


exc = JsonSchemaException('data must be smaller than or equal to 10')
@pytest.mark.parametrize('value, expected', [
    (-5, -5),
    (5, 5),
    (9, 9),
    (10, 10),
    (11, exc),
    (20, exc),
])
def test_maximum(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'maximum': 10,
    }, value, expected)


exc = JsonSchemaException('data must be smaller than 10')
@pytest.mark.parametrize('value, expected', [
    (-5, -5),
    (5, 5),
    (9, 9),
    (10, exc),
    (11, exc),
    (20, exc),
])
def test_exclusive_maximum(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'maximum': 10,
        'exclusiveMaximum': True,
    }, value, expected)


exc = JsonSchemaException('data must be bigger than or equal to 10')
@pytest.mark.parametrize('value, expected', [
    (-5, exc),
    (9, exc),
    (10, 10),
    (11, 11),
    (20, 20),
])
def test_minimum(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'minimum': 10,
    }, value, expected)


exc = JsonSchemaException('data must be bigger than 10')
@pytest.mark.parametrize('value, expected', [
    (-5, exc),
    (9, exc),
    (10, exc),
    (11, 11),
    (20, 20),
])
def test_exclusive_minimum(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'minimum': 10,
        'exclusiveMinimum': True,
    }, value, expected)


exc = JsonSchemaException('data must be multiple of 3')
@pytest.mark.parametrize('value, expected', [
    (-4, exc),
    (-3, -3),
    (-2, exc),
    (-1, exc),
    (0, 0),
    (1, exc),
    (2, exc),
    (3, 3),
    (4, exc),
    (5, exc),
    (6, 6),
    (7, exc),
])
def test_multiple_of(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'multipleOf': 3,
    }, value, expected)
