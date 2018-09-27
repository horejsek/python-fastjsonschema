import pytest


@pytest.mark.parametrize('value', (
    'foo',
    42,
    False,
    [1, 2, 3]
))
def test_const(asserter, value):
    asserter({
        '$schema': 'http://json-schema.org/draft-06/schema',
        'const': value,
    }, value, value)
