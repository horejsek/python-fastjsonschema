
import pytest

from fastjsonschema import JsonSchemaException


@pytest.mark.parametrize('value, expected', [
    (
        [9, 'hello', [1, 'a', True], {'a': 'a', 'b': 'b', 'd': 'd'}, 42, 3],
        [9, 'hello', [1, 'a', True], {'a': 'a', 'b': 'b', 'c': 'abc', 'd': 'd'}, 42, 3],
    ),
    (
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'd': 'd'}, 42, 3],
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'abc', 'd': 'd'}, 42, 3],
    ),
    (
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 42, 3],
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 42, 3],
    ),
    (
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
    ),
    (
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5, 'any'],
        [9, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5, 'any'],
    ),
    (
        [10, 'world', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        JsonSchemaException('data[0] must be smaller than 10'),
    ),
    (
        [9, 'xxx', [1], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        JsonSchemaException('data[1] must be one of [\'hello\', \'world\']'),
    ),
    (
        [9, 'hello', [], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        JsonSchemaException('data[2] must contain at least 1 items'),
    ),
    (
        [9, 'hello', [1, 2, 3], {'a': 'a', 'b': 'b', 'c': 'xy'}, 'str', 5],
        JsonSchemaException('data[2][1] must be string'),
    ),
    (
        [9, 'hello', [1], {'a': 'a', 'x': 'x', 'y': 'y'}, 'str', 5],
        JsonSchemaException('data[3] must contain [\'b\'] properties'),
    ),
    (
        [9, 'hello', [1], {}, 'str', 5],
        JsonSchemaException('data[3] must contain at least 3 properties'),
    ),
    (
        [9, 'hello', [1], {'a': 'a', 'b': 'b', 'x': 'x'}, None, 5],
        JsonSchemaException('data[4] must not be valid by not definition'),
    ),
    (
        [9, 'hello', [1], {'a': 'a', 'b': 'b', 'x': 'x'}, 42, 15],
        JsonSchemaException('data[5] must be valid exactly by one of oneOf definition'),
    ),
])
def test_integration(asserter, value, expected):
    asserter({
        'type': 'array',
        'items': [
            {
                'type': 'number',
                'maximum': 10,
                'exclusiveMaximum': True,
            },
            {
                'type': 'string',
                'enum': ['hello', 'world'],
            },
            {
                'type': 'array',
                'minItems': 1,
                'maxItems': 3,
                'items': [
                    {'type': 'number'},
                    {'type': 'string'},
                    {'type': 'boolean'},
                ],
            },
            {
                'type': 'object',
                'required': ['a', 'b'],
                'minProperties': 3,
                'properties': {
                    'a': {'type': ['null', 'string']},
                    'b': {'type': ['null', 'string']},
                    'c': {'type': ['null', 'string'], 'default': 'abc'}
                },
                'additionalProperties': {'type': 'string'},
            },
            {'not': {'type': ['null']}},
            {'oneOf': [
                {'type': 'number', 'multipleOf': 3},
                {'type': 'number', 'multipleOf': 5},
            ]},
        ],
    }, value, expected)


def test_any_of_with_patterns(asserter):
    asserter({
        'type': 'object',
        'properties': {
            'hash': {
                'anyOf': [
                    {
                        'type': 'string',
                        'pattern': '^AAA'
                    },
                    {
                        'type': 'string',
                        'pattern': '^BBB'
                    }
                ]
            }
        }
    }, {
        'hash': 'AAAXXX',
    }, {
        'hash': 'AAAXXX',
    })
