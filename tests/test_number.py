import decimal

import pytest

from fastjsonschema import JsonSchemaValueException, JsonSchemaValuesException, compile, compile_to_code


@pytest.fixture(params=['number', 'integer'])
def number_type(request):
    return request.param


exc = JsonSchemaValueException('data must be {number_type}')
@pytest.mark.parametrize('value, expected', [
    (-5, -5),
    (0, 0),
    (5, 5),
    (None, exc),
    (True, exc),
    ('abc', exc),
    ([], exc),
    ({}, exc),
])
def test_number(asserter, number_type, value, expected):
    if isinstance(expected, JsonSchemaValueException):
        expected = JsonSchemaValueException(expected.message.format(number_type=number_type), value='{data}', name='data', definition='{definition}', rule='type')
    asserter({'type': number_type}, value, expected)


exc = JsonSchemaValueException('data must be smaller than or equal to 10', value='{data}', name='data', definition='{definition}', rule='maximum')
@pytest.mark.parametrize('value, expected', [
    (-5, -5),
    (5, 5),
    (9, 9),
    (10, 10),
    (11, exc),
    (20, exc),
])
def test_maximum(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'maximum': 10,
    }, value, expected)


exc = JsonSchemaValueException('data must be smaller than 10', value='{data}', name='data', definition='{definition}', rule='maximum')
@pytest.mark.parametrize('value, expected', [
    (-5, -5),
    (5, 5),
    (9, 9),
    (10, exc),
    (11, exc),
    (20, exc),
])
def test_exclusive_maximum(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'maximum': 10,
        'exclusiveMaximum': True,
    }, value, expected)


exc = JsonSchemaValueException('data must be bigger than or equal to 10', value='{data}', name='data', definition='{definition}', rule='minimum')
@pytest.mark.parametrize('value, expected', [
    (-5, exc),
    (9, exc),
    (10, 10),
    (11, 11),
    (20, 20),
])
def test_minimum(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'minimum': 10,
    }, value, expected)


exc = JsonSchemaValueException('data must be bigger than 10', value='{data}', name='data', definition='{definition}', rule='minimum')
@pytest.mark.parametrize('value, expected', [
    (-5, exc),
    (9, exc),
    (10, exc),
    (11, 11),
    (20, 20),
])
def test_exclusive_minimum(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'minimum': 10,
        'exclusiveMinimum': True,
    }, value, expected)


exc = JsonSchemaValueException('data must be multiple of 3', value='{data}', name='data', definition='{definition}', rule='multipleOf')
@pytest.mark.parametrize('value, expected', [
    (-4, exc),
    (-3, -3),
    (-2, exc),
    (-1, exc),
    (0, 0),
    (1, exc),
    (2, exc),
    (3, 3),
    (4, exc),
    (5, exc),
    (6, 6),
    (7, exc),
])
def test_multiple_of(asserter, number_type, value, expected):
    asserter({
        'type': number_type,
        'multipleOf': 3,
    }, value, expected)


@pytest.fixture(params=[compile, compile_to_code], ids=['compiled', 'generated'])
def multiple_of_compiler(request):
    def generate(definition, fast_fail):
        validator = request.param(definition, fast_fail=fast_fail)
        if isinstance(validator, str):
            namespace = {}
            exec(validator, namespace)
            return namespace['validate']
        return validator
    return generate


@pytest.mark.parametrize('schema_version', ['04', '06', '07'])
@pytest.mark.parametrize('fast_fail', [True, False])
@pytest.mark.parametrize('divisor, value, valid', [
    (2, 2 ** 53 + 1, False),
    (2, -(2 ** 53 + 1), False),
    (2, 2 ** 63 - 1, False),
    (2, 2 ** 63 - 2, True),
    (3, 3 * 10 ** 400, True),
    (3, -3 * 10 ** 400, True),
    (3, 3 * 10 ** 400 + 1, False),
    (3, -(3 * 10 ** 400 + 1), False),
    (10 ** 400 + 3, 2 * (10 ** 400 + 3), True),
    (10 ** 400 + 3, 2 * (10 ** 400 + 3) + 1, False),
    (3, 0, True),
    (1, 10 ** 400, True),
], ids=[
    'above-float-precision', 'negative-above-float-precision',
    'signed-64-bit-odd', 'signed-64-bit-even',
    'huge-multiple', 'negative-huge-multiple',
    'huge-nonmultiple', 'negative-huge-nonmultiple',
    'huge-divisor-multiple', 'huge-divisor-nonmultiple', 'zero', 'unit-divisor',
])
def test_multiple_of_large_integers(multiple_of_compiler, schema_version, fast_fail, divisor, value, valid):
    definition = {
        '$schema': 'http://json-schema.org/draft-{}/schema'.format(schema_version),
        'type': 'integer',
        'multipleOf': divisor,
    }
    validator = multiple_of_compiler(definition, fast_fail)
    if valid:
        assert validator(value) == value
    else:
        exception = JsonSchemaValueException if fast_fail else JsonSchemaValuesException
        with pytest.raises(exception) as exc:
            validator(value)
        errors = [exc.value] if fast_fail else exc.value.errors
        assert len(errors) == 1
        assert errors[0].rule == 'multipleOf'
        assert errors[0].value == value
        assert errors[0].name == 'data'
        assert errors[0].definition == definition


@pytest.mark.parametrize('divisor, value, valid', [
    (3, 6.0, True),
    (3, 4.5, False),
    (3, decimal.Decimal('6'), True),
    (3, decimal.Decimal('4.5'), False),
    (0.01, 19.01, True),
    (0.01, 19.001, False),
    (decimal.Decimal('3'), 6, True),
    (decimal.Decimal('3'), 4, False),
])
def test_multiple_of_non_integer_operands(multiple_of_compiler, divisor, value, valid):
    validator = multiple_of_compiler({'multipleOf': divisor}, True)
    if valid:
        assert validator(value) == value
    else:
        with pytest.raises(JsonSchemaValueException):
            validator(value)


exc = JsonSchemaValueException('data must be multiple of 0.0001', value='{data}', name='data', definition='{definition}', rule='multipleOf')
@pytest.mark.parametrize('value, expected', [
    (0.00751, exc),
    (0.0075, 0.0075),
])
def test_multiple_of_float(asserter, value, expected):
    asserter({
        'type': 'number',
        'multipleOf': 0.0001,
    }, value, expected)


exc = JsonSchemaValueException('data must be multiple of 0.01', value='{data}', name='data', definition='{definition}', rule='multipleOf')
@pytest.mark.parametrize('value, expected', [
    (0, 0),
    (0.01, 0.01),
    (0.1, 0.1),
    (19.01, 19.01),
    (0.001, exc),
    (19.001, exc),
])
def test_multiple_of_float_1_5(asserter, value, expected):
    asserter({
        'type': 'number',
        'multipleOf': 0.01,
    }, value, expected)


@pytest.mark.parametrize('schema_version', (
    'http://json-schema.org/draft-04/schema',
    'http://json-schema.org/draft-06/schema',
    'http://json-schema.org/draft-07/schema',
))
@pytest.mark.parametrize('keywords', (
    {'minimum': 5},
    {'maximum': -5},
    {'multipleOf': 3},
))
@pytest.mark.parametrize('value', (True, False))
def test_numeric_keywords_ignore_boolean(asserter, schema_version, keywords, value):
    asserter({
        '$schema': schema_version,
        'type': ['boolean', 'number'],
        **keywords,
    }, value, value)


@pytest.mark.parametrize('schema_version', (
    'http://json-schema.org/draft-06/schema',
    'http://json-schema.org/draft-07/schema',
))
@pytest.mark.parametrize('keywords', (
    {'exclusiveMinimum': 5},
    {'exclusiveMaximum': -5},
))
@pytest.mark.parametrize('value', (True, False))
def test_exclusive_numeric_keywords_ignore_boolean(asserter, schema_version, keywords, value):
    asserter({
        '$schema': schema_version,
        'type': ['boolean', 'number'],
        **keywords,
    }, value, value)


@pytest.mark.parametrize('value', (
    1.0,
    0.1,
    0.01,
    0.001,
))
def test_integer_is_not_number(asserter, value):
    asserter({
        'type': 'integer',
    }, value, JsonSchemaValueException('data must be integer', value='{data}', name='data', definition='{definition}', rule='type'))


@pytest.mark.parametrize('value', (
    1.0,
    0.1,
    0.01,
    0.001,
))
def test_number_allows_float(asserter, value):
    asserter({
        'type': 'number',
    }, value, value)



@pytest.mark.parametrize('value', (
    decimal.Decimal('1.0'),
    decimal.Decimal('0.1'),
    decimal.Decimal('0.01'),
    decimal.Decimal('0.001'),
))
def test_number_allows_decimal(asserter, value):
    asserter({
        'type': 'number',
    }, value, value)
