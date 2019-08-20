from builtins import ValueError

import datetime

import pytest

import re

from fastjsonschema import JsonSchemaException


exc = JsonSchemaException('data must be date-time')
@pytest.mark.parametrize('value, expected', [
    ('', exc),
    ('bla', exc),
    ('2018-02-05T14:17:10.00', exc),
    ('2018-02-05T14:17:10.00Z\n', exc),
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
    ('example.example.com\n', exc),
    ('localhost', 'localhost'),
    ('example.com', 'example.com'),
    ('example.de', 'example.de'),
    ('example.fr', 'example.fr'),
    ('example.example.com', 'example.example.com'),
])
def test_hostname(asserter, value, expected):
    asserter({'type': 'string', 'format': 'hostname'}, value, expected)


def __special_timestamp_format_checker(date_string: str) -> bool:
    dt = datetime.datetime.fromisoformat(date_string).replace(tzinfo=datetime.timezone.utc)
    dt_now = datetime.datetime.now(datetime.timezone.utc)
    if dt > dt_now:
        raise ValueError(f"{date_string} is in the future")
    return True


pattern = "^(19|20)[0-9][0-9]-(0[1-9]|1[012])-(0[1-9]|[12][0-9]|3[01]) (0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]):([" \
              "0-5][0-9])\\.[0-9]{6}$ "


exc = JsonSchemaException('data is not a valid data')
@pytest.mark.parametrize('value, expected, formats', [
    ('', exc, {"special-timestamp": __special_timestamp_format_checker}),
    ('bla', exc, {"special-timestamp": __special_timestamp_format_checker}),
    ('2018-02-05T14:17:10.00', exc, {"special-timestamp": __special_timestamp_format_checker}),
    ('2019-03-12 13:08:03.001000\n', exc, {"special-timestamp": __special_timestamp_format_checker}),
    ('2999-03-12 13:08:03.001000', '2999-03-12 13:08:03.001000', exc, {"special-timestamp": __special_timestamp_format_checker}),
    ('2019-03-12 13:08:03.001000', '2019-03-12 13:08:03.001000', {"special-timestamp": __special_timestamp_format_checker}),
    ('2019-03-12 13:08:03.001000', '2019-03-12 13:08:03.001000', {"special-timestamp": pattern}),
    ('2019-03-12 13:08:03.001000', '2019-03-12 13:08:03.001000', {"special-timestamp": re.compile(pattern)}),
])
def test_special_datetime(asserter, value, expected, formats):
    asserter({'type': 'string', 'format': 'special-timestamp'}, value, expected, formats=formats)
