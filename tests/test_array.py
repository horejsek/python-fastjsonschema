
import pytest

from fastjsonschema import JsonSchemaException


exc = JsonSchemaException('data must be array')
@pytest.mark.parametrize('value, expected', [
    (0, exc),
    (None, exc),
    (True, exc),
    (False, exc),
    ('abc', exc),
    ([], []),
    ([1, 'a', True], [1, 'a', True]),
    ({}, exc),
])
def test_array(asserter, value, expected):
    asserter({'type': 'array'}, value, expected)


exc = JsonSchemaException('data must contain less than or equal to 1 items')
@pytest.mark.parametrize('value, expected', [
    ([], []),
    ([1], [1]),
    ([1, 1], exc),
    ([1, 2, 3], exc),
])
def test_max_items(asserter, value, expected):
    asserter({
        'type': 'array',
        'maxItems': 1,
    }, value, expected)


exc = JsonSchemaException('data must contain at least 2 items')
@pytest.mark.parametrize('value, expected', [
    ([], exc),
    ([1], exc),
    ([1, 1], [1, 1]),
    ([1, 2, 3], [1, 2, 3]),
])
def test_min_items(asserter, value, expected):
    asserter({
        'type': 'array',
        'minItems': 2,
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ([], []),
    ([1], [1]),
    ([1, 1], JsonSchemaException('data must contain unique items')),
    ([1, 2, 3], [1, 2, 3]),
])
def test_unique_items(asserter, value, expected):
    asserter({
        'type': 'array',
        'uniqueItems': True,
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ([], []),
    ([1], [1]),
    ([1, 'a'], JsonSchemaException('data[1] must be number')),
])
def test_items_all_same(asserter, value, expected):
    asserter({
        'type': 'array',
        'items': {'type': 'number'},
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ([], []),
    ([1], [1]),
    ([1, 'a'], [1, 'a']),
    ([1, 2], JsonSchemaException('data[1] must be string')),
    ([1, 'a', 2], [1, 'a', 2]),
    ([1, 'a', 'b'], [1, 'a', 'b']),
])
def test_different_items(asserter, value, expected):
    asserter({
        'type': 'array',
        'items': [
            {'type': 'number'},
            {'type': 'string'},
        ],
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ([], []),
    ([1], [1]),
    ([1, 'a'], [1, 'a']),
    ([1, 2], JsonSchemaException('data[1] must be string')),
    ([1, 'a', 2], JsonSchemaException('data[2] must be string')),
    ([1, 'a', 'b'], [1, 'a', 'b']),
])
def test_different_items_with_additional_items(asserter, value, expected):
    asserter({
        'type': 'array',
        'items': [
            {'type': 'number'},
            {'type': 'string'},
        ],
        'additionalItems': {'type': 'string'},
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ([], []),
    ([1], [1]),
    ([1, 'a'], [1, 'a']),
    ([1, 2], JsonSchemaException('data[1] must be string')),
    ([1, 'a', 2], JsonSchemaException('data must contain only specified items')),
    ([1, 'a', 'b'], JsonSchemaException('data must contain only specified items')),
])
def test_different_items_without_additional_items(asserter, value, expected):
    asserter({
        'type': 'array',
        'items': [
            {'type': 'number'},
            {'type': 'string'},
        ],
        'additionalItems': False,
    }, value, expected)
