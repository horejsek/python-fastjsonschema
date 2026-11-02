import pytest

from fastjsonschema import (
    JsonSchemaValueException, JsonSchemaValuesException, compile, compile_to_code,
)


@pytest.mark.parametrize('value, testError', (
    ('foo', False),
    (42, False),
    (False, False),
    ([1, 2, 3], False),
    ('\'"', False),
    ('foo', True),
    ('\'"', False),
))
def test_const(asserter, value, testError):
    const = expected = value
    if testError:
        const = 'x'
        expected = JsonSchemaValueException('data must be same as const definition: x', value='{data}', name='data', definition='{definition}', rule='const')
    
    asserter({
        '$schema': 'http://json-schema.org/draft-06/schema',
        'const': const,
    }, value, expected)


@pytest.mark.parametrize('draft', ('06', '07'))
@pytest.mark.parametrize('detailed_exceptions', (True, False))
@pytest.mark.parametrize('fast_fail', (True, False))
@pytest.mark.parametrize('matches', (True, False))
@pytest.mark.parametrize('const, invalid, message_value', (
    ('foo', 'bar', 'foo'),
    ('\'"', 'other', '\'"'),
    (42, 43, '42'),
    (1.5, 1.6, '1.5'),
    (True, False, 'True'),
    (None, 0, 'None'),
    ([1, 'x'], [2, 'x'], "[1, 'x']"),
    ({'key': 'value'}, {'key': 'other'}, "{'key': 'value'}"),
))
def test_const_exception_options(draft, detailed_exceptions, fast_fail, matches,
                                 const, invalid, message_value):
    validator = compile({
        '$schema': 'http://json-schema.org/draft-{}/schema#'.format(draft),
        'const': const,
    }, detailed_exceptions=detailed_exceptions, fast_fail=fast_fail)

    if matches:
        assert validator(const) is const
    else:
        exception = JsonSchemaValueException if fast_fail else JsonSchemaValuesException
        with pytest.raises(exception) as exc:
            validator(invalid)
        expected_message = 'data must be same as const definition: ' + message_value
        assert exc.value.message == expected_message
        if not fast_fail:
            assert len(exc.value.errors) == 1
            assert isinstance(exc.value.errors[0], JsonSchemaValueException)
            assert exc.value.errors[0].message == expected_message


@pytest.mark.parametrize('detailed_exceptions', (True, False))
@pytest.mark.parametrize('fast_fail', (True, False))
def test_const_compile_to_code_exception_options(detailed_exceptions, fast_fail):
    code = compile_to_code({'const': 1}, detailed_exceptions=detailed_exceptions,
                           fast_fail=fast_fail)
    scope = {}
    exec(code, scope)

    assert scope['validate'](1) == 1
    exception = JsonSchemaValueException if fast_fail else JsonSchemaValuesException
    with pytest.raises(exception) as exc:
        scope['validate'](2)
    assert exc.value.message == 'data must be same as const definition: 1'


@pytest.mark.parametrize('fast_fail', (True, False))
@pytest.mark.parametrize('to_code', (True, False))
def test_compact_exceptions_ignore_refs_in_examples(fast_fail, to_code):
    schema = {
        '$schema': 'http://json-schema.org/draft-07/schema#',
        'type': 'object',
        'examples': [{'$ref': '#/missing'}],
    }
    if to_code:
        code = compile_to_code(schema, detailed_exceptions=False, fast_fail=fast_fail)
        scope = {}
        exec(code, scope)
        validator = scope['validate']
    else:
        validator = compile(schema, detailed_exceptions=False, fast_fail=fast_fail)

    value = {'hello': 'world'}
    assert validator(value) is value
