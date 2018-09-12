import pytest

from fastjsonschema import JsonSchemaException


exc = JsonSchemaException('data must be hostname')
@pytest.mark.parametrize('value, expected', [
    ('', exc),
    ('LDhsjf878&d', exc),
    ('bla.bla-', exc),
    ('example.example.com-', exc),
    ('localhost', 'localhost'),
    ('example.com', 'example.com'),
    ('example.de', 'example.de'),
    ('example.fr', 'example.fr'),
    ('example.example.com', 'example.example.com'),
])
def test_datetime(asserter, value, expected):
    asserter({'type': 'string', 'format': 'hostname'}, value, expected)
