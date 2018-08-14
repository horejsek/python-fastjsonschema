import pytest

from .utils import template_test, resolve_param_values_and_ids


def pytest_generate_tests(metafunc):
    param_values, param_ids = resolve_param_values_and_ids(
        version=6,
        suite_dir='JSON-Schema-Test-Suite/tests/draft6',
        ignored_suite_files=[
            'ecmascript-regex.json',
            'boolean_schema.json',
        ],
        ignore_tests=[
            'invalid definition',
            'valid definition',
            'Recursive references between schemas',
            'remote ref, containing refs itself',
            'validation of URI References',
            'items with boolean schemas',
            'not with boolean schema true',
            'not with boolean schema false',
            'properties with boolean schema',
            'base URI change - change folder',
            'base URI change - change folder in subschema',
            'base URI change',
            'root ref in remote ref',
            'validation of JSON-pointers (JSON String Representation)',
        ],
    )
    metafunc.parametrize(['version', 'schema', 'data', 'is_valid'], param_values, ids=param_ids)


# Real test function to be used with parametrization by previous hook function.
test = template_test
