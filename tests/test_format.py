import datetime
import re

import pytest

from fastjsonschema import JsonSchemaValueException


exc = JsonSchemaValueException('data must be date-time', value='{data}', name='data', definition='{definition}', rule='format')
@pytest.mark.parametrize('value, expected', [
    ('', exc),
    ('bla', exc),
    ('2018-02-05T14:17:10.00', exc),
    ('2018-02-05T14:17:10.00Z\n', exc),
    ('2018-02-05T14:17:10.00Z', '2018-02-05T14:17:10.00Z'),
    ('2018-02-05T14:17:10Z', '2018-02-05T14:17:10Z'),
    ('2020-09-09T01:01:01+0100', '2020-09-09T01:01:01+0100'),
])
def test_datetime(asserter, value, expected):
    asserter({'type': 'string', 'format': 'date-time'}, value, expected)


exc = JsonSchemaValueException('data must be hostname', value='{data}', name='data', definition='{definition}', rule='format')
@pytest.mark.parametrize('value, expected', [
    ('', exc),
    ('LDhsjf878&d', exc),
    ('bla.bla-', exc),
    ('example.example.com-', exc),
    ('example.example.com\n', exc),
    ('localhost', 'localhost'),
    ('example.com', 'example.com'),
    ('example.de', 'example.de'),
    ('example.fr', 'example.fr'),
    ('example.example.com', 'example.example.com'),
])
def test_hostname(asserter, value, expected):
    asserter({'type': 'string', 'format': 'hostname'}, value, expected)


exc = JsonSchemaValueException('data must be custom-format', value='{data}', name='data', definition='{definition}', rule='format')
@pytest.mark.parametrize('value,expected,custom_format', [
    ('', exc, r'^[ab]$'),
    ('', exc, lambda value: value in ('a', 'b')),
    ('a', 'a', r'^[ab]$'),
    ('a', 'a', lambda value: value in ('a', 'b')),
    ('c', exc, r'^[ab]$'),
    ('c', exc, lambda value: value in ('a', 'b')),
])
def test_custom_format(asserter, value, expected, custom_format):
    asserter({'format': 'custom-format'}, value, expected, formats={
        'custom-format': custom_format,
    })


def test_custom_format_override(asserter):
    asserter({'format': 'date-time'}, 'a', 'a', formats={
        'date-time': r'^[ab]$',
    })
