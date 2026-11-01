import pytest

from fastjsonschema import JsonSchemaValueException, compile, compile_to_code
from fastjsonschema.ref_resolver import RefResolver, resolve_path


@pytest.mark.parametrize('fragment, expected', [
    ('/', {'child': 1, '': 2, 'a/b': 3, '~': 4, 'café': 5}),
    ('//child', 1),
    ('//', 2),
    ('//a~1b', 3),
    ('//~0', 4),
    ('//caf%C3%A9', 5),
])
def test_empty_leading_pointer_tokens(fragment, expected):
    schema = {'': {'child': 1, '': 2, 'a/b': 3, '~': 4, 'café': 5}}
    assert resolve_path(schema, fragment) == expected


def test_root_and_ordinary_pointer_tokens():
    schema = {'items': [{'type': 'integer'}]}
    assert resolve_path(schema, '') is schema
    assert resolve_path(schema, '/items/0') == {'type': 'integer'}
    assert resolve_path(schema, 'items/0') == {'type': 'integer'}


@pytest.mark.parametrize('generated', [False, True])
@pytest.mark.parametrize('ref, subschema', [
    ('#/', {'type': 'integer'}),
    ('#//child', {'child': {'type': 'integer'}}),
    ('#//', {'': {'type': 'integer'}}),
])
def test_compile_references_through_empty_root_key(generated, ref, subschema):
    schema = {
        '': subschema,
        'type': 'object',
        'properties': {'value': {'$ref': ref}},
    }
    if generated:
        namespace = {}
        exec(compile_to_code(schema), namespace)
        validator = namespace['validate']
    else:
        validator = compile(schema)

    assert validator({'value': 42}) == {'value': 42}
    with pytest.raises(JsonSchemaValueException):
        validator({'value': 'wrong type'})


@pytest.mark.parametrize('generated', [False, True])
def test_empty_key_in_handler_loaded_schema(generated):
    remote = {
        '': {'type': 'integer'},
        'type': 'object',
        'properties': {'value': {'$ref': '#/'}},
    }
    schema = {'$ref': 'https://schemas.example/schema.json'}
    handlers = {'https': lambda _uri: remote}
    if generated:
        namespace = {}
        exec(compile_to_code(schema, handlers=handlers), namespace)
        validator = namespace['validate']
    else:
        validator = compile(schema, handlers=handlers)

    assert validator({'value': 42}) == {'value': 42}
    with pytest.raises(JsonSchemaValueException):
        validator({'value': 'wrong type'})


def test_empty_key_scope_names_stay_unique_and_stable():
    resolver = RefResolver.from_schema({})
    root_name = resolver.get_scope_name()
    with resolver.in_scope('#/'):
        child_name = resolver.get_scope_name()
        assert resolver.get_scope_name() == child_name
    with resolver.in_scope('#//'):
        grandchild_name = resolver.get_scope_name()
    with resolver.in_scope('#'):
        assert resolver.get_scope_name() == root_name
    assert len({root_name, child_name, grandchild_name}) == 3
