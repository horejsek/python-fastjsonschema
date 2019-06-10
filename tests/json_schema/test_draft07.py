import pytest

from .utils import template_test, resolve_param_values_and_ids


def pytest_generate_tests(metafunc):
    param_values, param_ids = resolve_param_values_and_ids(
        schema_version='http://json-schema.org/draft-07/schema',
        suite_dir='JSON-Schema-Test-Suite/tests/draft7',
        ignored_suite_files=[
            # Optional.
            'ecmascript-regex.json',
            'idn-hostname.json',
            'iri.json',
        ],
    )
    metafunc.parametrize(['schema_version', 'schema', 'data', 'is_valid'], param_values, ids=param_ids)


# Real test function to be used with parametrization by previous hook function.
test = template_test
