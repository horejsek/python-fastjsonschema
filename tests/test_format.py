import pytest

from fastjsonschema import JsonSchemaException


exc = JsonSchemaException('data must be date-time')
@pytest.mark.parametrize('value, expected', [
    ('', exc),
    ('bla', exc),
    ('2018-02-05T14:17:10.00Z', '2018-02-05T14:17:10.00Z'),
    ('2018-02-05T14:17:10Z', '2018-02-05T14:17:10Z'),
])
def test_datetime(asserter, value, expected):
    asserter({'type': 'string', 'format': 'date-time'}, value, expected)


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
def test_hostname(asserter, value, expected):
    asserter({'type': 'string', 'format': 'hostname'}, value, expected)
