import warnings

import pytest

from fastjsonschema import JsonSchemaValueException


def test_dont_override_variable_names(asserter):
    value = {
        'foo:bar': {
            'baz': {
                'bat': {},
            },
            'bit': {},
        },
    }
    asserter({
        'type': 'object',
        'patternProperties': {
            '^foo:': {
                'type': 'object',
                'properties': {
                    'baz': {
                        'type': 'object',
                        'patternProperties': {
                            '^b': {'type': 'object'},
                        },
                    },
                    'bit': {'type': 'object'},
                },
            },
        },
    }, value, value)


def test_clear_variables(asserter):
    value = {
        'bar': {'baz': 'foo'}
    }
    asserter({
        'type': 'object',
        'patternProperties': {
            'foo': {'type': 'object', 'required': ['baz']},
            'bar': {'type': 'object', 'required': ['baz']}
        }
    }, value, value)


def test_pattern_with_escape(asserter):
    value = {
        '\\n': {}
    }
    asserter({
        'type': 'object',
        'patternProperties': {
            '\\\\n': {'type': 'object'}
        }
    }, value, value)


def test_pattern_with_escape_no_warnings(asserter):
    value = {
        'bar': {}
    }

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        asserter({
            'type': 'object',
            'patternProperties': {
                '\\w+': {'type': 'object'}
            }
        }, value, value)

def test_empty_pattern(asserter):
    value = {}
    asserter({
        'type': 'object',
        'patternProperties': {}
    }, value, value)


@pytest.mark.parametrize('value, expected', [
    ({'abc': 1}, {'abc': 1}),
    ({'abc\n': 1}, JsonSchemaValueException('data must not contain {\'abc\\n\'} properties', value='{data}', name='data', definition='{definition}', rule='additionalProperties')),
])
def test_pattern_dollar_does_not_match_trailing_newline(asserter, value, expected):
    asserter({
        'type': 'object',
        'patternProperties': {
            '^[a-z]+$': {},
        },
        'additionalProperties': False,
    }, value, expected)


@pytest.mark.parametrize('value, expected', [
    ('abc', 'abc'),
    ('abc\n', JsonSchemaValueException('data must match pattern ^[a-z]+$', value='{data}', name='data', definition='{definition}', rule='pattern')),
])
def test_pattern_shared_with_pattern_properties(asserter, value, expected):
    asserter({
        'pattern': '^[a-z]+$',
        'patternProperties': {
            '^[a-z]+$': {},
        },
    }, value, expected)
