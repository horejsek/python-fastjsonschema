import json
from pathlib import Path

import pytest
import requests

from fastjsonschema import CodeGenerator, JsonSchemaException, compile

remotes = {
    "http://localhost:1234/integer.json": {u"type": u"integer"},
    "http://localhost:1234/name.json": {
        u"type": "string",
        u"definitions": {
            u"orNull": {u"anyOf": [{u"type": u"null"}, {u"$ref": u"#"}]},
        },
    },
    "http://localhost:1234/subSchemas.json": {
        u"integer": {u"type": u"integer"},
        u"refToInteger": {u"$ref": u"#/integer"},
    },
    "http://localhost:1234/folder/folderInteger.json": {u"type": u"integer"}
}
def remotes_handler(uri):
    if uri in remotes:
        return remotes[uri]
    return requests.get(uri).json()

def pytest_generate_tests(metafunc):
    suite_dir = 'JSON-Schema-Test-Suite/tests/draft4'
    ignored_suite_files = [
        'ecmascript-regex.json',
    ]
    ignore_tests = [
        "base URI change - change folder in subschema",
    ]

    suite_dir_path = Path(suite_dir).resolve()
    test_file_paths = sorted(set(suite_dir_path.glob("**/*.json")))

    param_values = []
    param_ids = []

    for test_file_path in test_file_paths:
        with test_file_path.open() as test_file:
            test_cases = json.load(test_file)
            for test_case in test_cases:
                for test_data in test_case['tests']:
                    param_values.append(pytest.param(
                        test_case['schema'],
                        test_data['data'],
                        test_data['valid'],
                        marks=pytest.mark.xfail
                            if test_file_path.name in ignored_suite_files
                                or test_case['description'] in ignore_tests
                            else pytest.mark.none,
                    ))
                    param_ids.append('{} / {} / {}'.format(
                        test_file_path.name,
                        test_case['description'],
                        test_data['description'],
                    ))

    metafunc.parametrize(['schema', 'data', 'is_valid'], param_values, ids=param_ids)


def test(schema, data, is_valid):
    # For debug purposes. When test fails, it will print stdout.
    print(CodeGenerator(schema).func_code)

    validate = compile(schema, handlers={'http': remotes_handler})
    try:
        result = validate(data)
        print('Validate result:', result)
    except JsonSchemaException:
        if is_valid:
            raise
    else:
        if not is_valid:
            pytest.fail('Test should not pass')
