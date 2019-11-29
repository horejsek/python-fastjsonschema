import os
import pytest
import shutil

from fastjsonschema import compile_to_code, compile as compile_spec

@pytest.yield_fixture(autouse=True)
def run_around_tests():
    temp_dir = 'temp'
    # Code that will run before your test, for example:
    if not os.path.isdir(temp_dir):
        os.makedirs(temp_dir)
    # A test function will be run at this point
    yield
    # Code that will run after your test, for example:
    shutil.rmtree(temp_dir)


def test_compile_to_code():
    code = compile_to_code({
        'properties': {
            'a': {'type': 'string'},
            'b': {'type': 'integer'},
            'c': {'format': 'hostname'},  # Test generation of regex patterns to the file.
        }
    })
    with open('temp/schema_1.py', 'w') as f:
        f.write(code)
    from temp.schema_1 import validate
    assert validate({
        'a': 'a',
        'b': 1, 
        'c': 'example.com',
    }) == {
        'a': 'a',
        'b': 1,
        'c': 'example.com',
    }

def test_compile_to_code_ipv6_regex():
    code = compile_to_code({
        'properties': {
            'ip': {'format': 'ipv6'},
        }
    })
    with open('temp/schema_2.py', 'w') as f:
        f.write(code)
    from temp.schema_2 import validate
    assert validate({
        'ip': '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
    }) == {
        'ip': '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
    }

# https://github.com/horejsek/python-fastjsonschema/issues/74
def test_compile_complex_one_of_all_of():
    compile_spec({
        "oneOf": [
            {
                "required": [
                    "schema"
                ]
            },
            {
                "required": [
                    "content"
                ],
                "allOf": [
                    {
                        "not": {
                            "required": [
                                "style"
                            ]
                        }
                    },
                    {
                        "not": {
                            "required": [
                                "explode"
                            ]
                        }
                    }
                ]
            }
        ]
    })
