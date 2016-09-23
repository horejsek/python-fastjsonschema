
import pytest

from fastjsonschema import JsonSchemaException


exc = JsonSchemaException('data must be one of [1, 2, \'a\']')
@pytest.mark.parametrize('value, expected', [
    (1, 1),
    (2, 2),
    (12, exc),
    ('a', 'a'),
    ('aa', exc),
])
def test_enum(asserter, value, expected):
    asserter({'enum': [1, 2, 'a']}, value, expected)


exc = JsonSchemaException('data must be string or number')
@pytest.mark.parametrize('value, expected', [
    (0, 0),
    (None, exc),
    (True, exc),
    ('abc', 'abc'),
    ([], exc),
    ({}, exc),
])
def test_types(asserter, value, expected):
    asserter({'type': ['string', 'number']}, value, expected)


@pytest.mark.parametrize('value, expected', [
    ('qwert', 'qwert'),
    ('qwertz', JsonSchemaException('data must be shorter than or equal to 5 characters')),
])
def test_all_of(asserter, value, expected):
    asserter({'allOf': [
        {'type': 'string'},
        {'maxLength': 5},
    ]}, value, expected)


exc = JsonSchemaException('data must be valid by one of anyOf definition')
@pytest.mark.parametrize('value, expected', [
    (0, 0),
    (None, exc),
    (True, exc),
    ('abc', 'abc'),
    ([], exc),
    ({}, exc),
])
def test_any_of(asserter, value, expected):
    asserter({'anyOf': [
        {'type': 'string'},
        {'type': 'number'},
    ]}, value, expected)


exc = JsonSchemaException('data must be valid exactly by one of oneOf definition')
@pytest.mark.parametrize('value, expected', [
    (0, exc),
    (2, exc),
    (9, 9),
    (10, 10),
    (15, exc),
])
def test_one_of(asserter, value, expected):
    asserter({'oneOf': [
        {'type': 'number', 'multipleOf': 5},
        {'type': 'number', 'multipleOf': 3},
    ]}, value, expected)


exc = JsonSchemaException('data must be valid exactly by one of oneOf definition')
@pytest.mark.parametrize('value, expected', [
    (0, exc),
    (2, exc),
    (9, 9),
    (10, 10),
    (15, exc),
])
def test_one_of_factorized(asserter, value, expected):
    asserter({
        'type': 'number',
        'oneOf': [
            {'multipleOf': 5},
            {'multipleOf': 3},
        ],
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    (0, JsonSchemaException('data must not be valid by not definition')),
    (True, True),
    ('abc', 'abc'),
    ([], []),
    ({}, {}),
])
def test_not(asserter, value, expected):
    asserter({'not': {'type': 'number'}}, value, expected)
