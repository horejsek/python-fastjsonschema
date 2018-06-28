
import pytest

from fastjsonschema import JsonSchemaException


exc = JsonSchemaException('data must be string')
@pytest.mark.parametrize('value, expected', [
    (0, exc),
    (None, exc),
    (True, exc),
    ('', ''),
    ('abc', 'abc'),
    ([], exc),
    ({}, exc),
])
def test_string(asserter, value, expected):
    asserter({'type': 'string'}, value, expected)


exc = JsonSchemaException('data must be shorter than or equal to 5 characters')
@pytest.mark.parametrize('value, expected', [
    ('', ''),
    ('qwer', 'qwer'),
    ('qwert', 'qwert'),
    ('qwertz', exc),
    ('qwertzuiop', exc),
])
def test_max_length(asserter, value, expected):
    asserter({
        'type': 'string',
        'maxLength': 5,
    }, value, expected)


exc = JsonSchemaException('data must be longer than or equal to 5 characters')
@pytest.mark.parametrize('value, expected', [
    ('', exc),
    ('qwer', exc),
    ('qwert', 'qwert'),
    ('qwertz', 'qwertz'),
    ('qwertzuiop', 'qwertzuiop'),
])
def test_min_length(asserter, value, expected):
    asserter({
        'type': 'string',
        'minLength': 5,
    }, value, expected)


exc = JsonSchemaException('data must match pattern ^[ab]*[^ab]+(c{2}|d)$')
@pytest.mark.parametrize('value, expected', [
    ('', exc),
    ('aacc', exc),
    ('aaccc', 'aaccc'),
    ('aacd', 'aacd'),
])
def test_pattern(asserter, value, expected):
    asserter({
        'type': 'string',
        'pattern': '^[ab]*[^ab]+(c{2}|d)$',
    }, value, expected)

exc = JsonSchemaException('data must be a valid regex')
@pytest.mark.parametrize('value, expected', [
    ('[a-z]', '[a-z]'),
    ('[a-z', exc),
])
def test_regex_pattern(asserter, value, expected):
    asserter({
        'format': 'regex',
        'type': 'string'
    }, value, expected)
