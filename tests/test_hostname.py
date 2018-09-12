import pytest

from fastjsonschema import JsonSchemaException


exc = JsonSchemaException('data must be hostname')
@pytest.mark.parametrize('value, expected', [
    ('', exc),
    ('localhost', 'localhost'),
    ('example.com', 'example.com'),
    ('example.de', 'example.de'),
])
def test_datetime(asserter, value, expected):
    asserter({'type': 'string', 'format': 'hostname'}, value, expected)
