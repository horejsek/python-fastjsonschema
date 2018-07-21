import pytest

from .utils import template_test, resolve_param_values_and_ids


def pytest_generate_tests(metafunc):
    param_values, param_ids = resolve_param_values_and_ids(
        suite_dir='JSON-Schema-Test-Suite/tests/draft7',
        ignored_suite_files=[
            'bignum.json',
            'ecmascript-regex.json',
            'zeroTerminatedFloats.json',
            'boolean_schema.json',
            'contains.json',
            'content.json',
            'if-then-else.json',
            'idn-email.json',
            'idn-hostname.json',
            'iri-reference.json',
            'iri.json',
            'relative-json-pointer.json',
            'time.json',
            'const.json',
        ],
        ignore_tests=[
            'invalid definition',
            'valid definition',
            'Recursive references between schemas',
            'remote ref, containing refs itself',
            'dependencies with boolean subschemas',
            'dependencies with empty array',
            'exclusiveMaximum validation',
            'exclusiveMinimum validation',
            'format: uri-template',
            'validation of URI References',
            'items with boolean schema (true)',
            'items with boolean schema (false)',
            'items with boolean schema',
            'items with boolean schemas',
            'not with boolean schema true',
            'not with boolean schema false',
            'properties with boolean schema',
            'propertyNames with boolean schema false',
            'propertyNames validation',
            'base URI change - change folder',
            'base URI change - change folder in subschema',
            'base URI change',
            'root ref in remote ref',
            'validation of date strings',
            'allOf with boolean schemas, all true',
            'allOf with boolean schemas, some false',
            'allOf with boolean schemas, all false',
            'anyOf with boolean schemas, all true',
            'anyOf with boolean schemas, some false',
            'anyOf with boolean schemas, all false',
            'anyOf with boolean schemas, some true',
            'oneOf with boolean schemas, all true',
            'oneOf with boolean schemas, some false',
            'oneOf with boolean schemas, all false',
            'oneOf with boolean schemas, one true',
            'oneOf with boolean schemas, more than one true',
            'validation of JSON-pointers (JSON String Representation)',
            'patternProperties with boolean schemas',
            '$ref to boolean schema true',
            '$ref to boolean schema false',
        ],
    )
    metafunc.parametrize(['schema', 'data', 'is_valid'], param_values, ids=param_ids)


# Real test function to be used with parametrization by previous hook function.
test = template_test
