import os
import pytest

from fastjsonschema import JsonSchemaException, write_code

def test_write_code():
    if not os.path.isdir('temp'):
        os.makedirs('temp')
    if os.path.exists('temp/schema.py'):
        os.remove('temp/schema.py')
    name = write_code(
        'temp/schema.py',
        {'properties': {'a': {'type': 'string'}, 'b': {'type': 'integer'}}}
    )
    assert name == 'validate'
    assert os.path.exists('temp/schema.py')
    with pytest.raises(JsonSchemaException) as exc:
        name = write_code(
            'temp/schema.py',
            {'type': 'string'}
        )
        assert exc.value.message == 'file temp/schema.py already exists'
    from temp.schema import validate
    assert validate({'a': 'a', 'b': 1}) == {'a': 'a', 'b': 1}
