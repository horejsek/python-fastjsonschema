import os
import pytest

from fastjsonschema import JsonSchemaException, compile_to_code


def test_compile_to_code():
    code = compile_to_code({
        'properties': {
            'a': {'type': 'string'},
            'b': {'type': 'integer'},
            'c': {'format': 'hostname'},
        }
    })
    if not os.path.isdir('temp'):
        os.makedirs('temp')
    with open('temp/schema.py', 'w') as f:
        f.write(code)
    from temp.schema import validate
    assert validate({
        'a': 'a',
        'b': 1, 
        'c': 'example.com',
    }) == {
        'a': 'a',
        'b': 1,
        'c': 'example.com',
    }
