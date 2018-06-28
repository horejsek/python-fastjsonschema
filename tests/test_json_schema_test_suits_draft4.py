import pytest
from test_json_schema_test_suits import template_test, resolve_param_values_and_ids


def pytest_generate_tests(metafunc):
    suite_dir = 'JSON-Schema-Test-Suite/tests/draft4'
    ignored_suite_files = [
        'ecmascript-regex.json',
    ]
    ignore_tests = []

    param_values, param_ids = resolve_param_values_and_ids(
        suite_dir, ignored_suite_files, ignore_tests
    )
    metafunc.parametrize(['schema', 'data', 'is_valid'], param_values, ids=param_ids)

test = template_test
