import pytest

from fastjsonschema import JsonSchemaException


@pytest.mark.parametrize('value, expected', [
    ('data', ['data']),
    ('data[0]', ['data', '0']),
    ('data.foo', ['data', 'foo']),
    ('data[1].bar', ['data', '1', 'bar']),
    ('data.foo[2]', ['data', 'foo', '2']),
    ('data.foo.bar[1][2]', ['data', 'foo', 'bar', '1', '2']),
    ('data[1][2].foo.bar', ['data', '1', '2', 'foo', 'bar']),
])
def test_exception_variable_path(value, expected):
    exc = JsonSchemaException('msg', name=value)
    assert exc.path == expected
