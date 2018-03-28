import json
from pathlib import Path

import pytest

from fastjsonschema import CodeGenerator, JsonSchemaException, compile


def pytest_generate_tests(metafunc):
    suite_dir = 'JSON-Schema-Test-Suite/tests/draft4'
    ignored_suite_files = [
        'definitions.json',
        'dependencies.json',
        'bignum.json',
        'ecmascript-regex.json',
        'format.json',
        'zeroTerminatedFloats.json',
        'ref.json',
        'refRemote.json',
        'uniqueItems.json',
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
                        marks=pytest.mark.xfail if test_file_path.name in ignored_suite_files else pytest.mark.none,
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

    validate = compile(schema)
    try:
        result = validate(data)
        print('Validate result:', result)
    except JsonSchemaException:
        if is_valid:
            raise
    else:
        if not is_valid:
            pytest.fail('Test should not pass')
