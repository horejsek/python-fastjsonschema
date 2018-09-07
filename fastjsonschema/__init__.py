#    ___
#    \./     DANGER: This project implements some code generation
# .--.O.--.          techniques involving string concatenation.
#  \/   \/           If you look at it, you might die.
#

"""
This project was made to come up with fast JSON validations. Just let's see some numbers first:

 * Probalby most popular ``jsonschema`` can take in tests up to 5 seconds for valid inputs
   and 1.2 seconds for invalid inputs.
 * Secondly most popular ``json-spec`` is even worse with up to 7.2 and 1.7 seconds.
 * Lastly ``validictory`` is much better with 370 or 23 miliseconds, but it does not
   follow all standards and it can be still slow for some purposes.

That's why this project exists. It compiles definition into Python most stupid code
which people would had hard time to write by themselfs because of not-written-rule DRY
(don't repeat yourself). When you compile definition, then times are 25 miliseconds for
valid inputs and less than 2 miliseconds for invalid inputs. Pretty amazing, right? :-)

You can try it for yourself with included script:

.. code-block:: bash

    $ make performance
    fast_compiled        valid      ==> 0.030474655970465392
    fast_compiled        invalid    ==> 0.0017561429995112121
    fast_file            valid      ==> 0.028758891974575818
    fast_file            invalid    ==> 0.0017655809642747045
    fast_not_compiled    valid      ==> 4.597834145999514
    fast_not_compiled    invalid    ==> 1.139162228035275
    jsonschema           valid      ==> 5.014410221017897
    jsonschema           invalid    ==> 1.1362981660058722
    jsonspec             valid      ==> 8.1144932230236
    jsonspec             invalid    ==> 2.0143173419637606
    validictory          valid      ==> 0.4084212710149586
    validictory          invalid    ==> 0.026061681972350925

This library follows and implements `JSON schema draft-04, draft-06 and draft-07
<http://json-schema.org>`_. Sometimes it's not perfectly clear so I recommend also
check out this `understaning json schema <https://spacetelescope.github.io/understanding-json-schema>`_.

Note that there are some differences compared to JSON schema standard:

 * Regular expressions are full Python ones, not only what JSON schema allows. It's easier
   to allow everything and also it's faster to compile without limits. So keep in mind that when
   you will use more advanced regular expression, it may not work with other library or in
   other language.
 * JSON schema says you can use keyword ``default`` for providing default values. This implementation
   uses that and always returns transformed input data.

Support only for Python 3.3 and higher.
"""

from .draft04 import CodeGeneratorDraft04
from .draft06 import CodeGeneratorDraft06
from .draft07 import CodeGeneratorDraft07
from .exceptions import JsonSchemaException
from .ref_resolver import RefResolver
from .version import VERSION

__all__ = ('VERSION', 'JsonSchemaException', 'compile', 'compile_to_code')


# pylint: disable=redefined-builtin,dangerous-default-value,exec-used
def compile(definition, handlers={}):
    """
    Generates validation function for validating JSON schema by ``definition``. Example:

    .. code-block:: python

        import fastjsonschema

        validate = fastjsonschema.compile({'type': 'string'})
        validate('hello')

    This implementation support keyword ``default``:

    .. code-block:: python

        validate = fastjsonschema.compile({
            'type': 'object',
            'properties': {
                'a': {'type': 'number', 'default': 42},
            },
        })

        data = validate({})
        assert data == {'a': 42}

    Supported implementations are draft-04, draft-06 and draft-07. Which version
    should be used is determined by `$draft` in your ``definition``. When not
    specified, the latest implementation is used (draft-07).

    .. code-block:: python

        validate = fastjsonschema.compile({
            '$schema': 'http://json-schema.org/draft-04/schema',
            'type': 'number',
        })

    You can pass mapping from URI to function that should be used to retrieve
    remote schemes used in your ``definition`` in parameter ``handlers``.

    Exception :any:`JsonSchemaException` is thrown when validation fails.
    """
    resolver, code_generator = _factory(definition, handlers)
    global_state = code_generator.global_state
    # Do not pass local state so it can recursively call itself.
    exec(code_generator.func_code, global_state)
    return global_state[resolver.get_scope_name()]


# pylint: disable=dangerous-default-value
def compile_to_code(definition, handlers={}):
    """
    Generates validation function for validating JSON schema by ``definition``
    and returns compiled code. Example:

    .. code-block:: python

        import fastjsonschema

        code = fastjsonschema.compile_to_code({'type': 'string'})
        with open('your_file.py', 'w') as f:
            f.write(code)

    You can also use it as a script:

    .. code-block:: bash

        echo "{'type': 'string'}" | python3 -m fastjsonschema > your_file.py
        python3 -m fastjsonschema "{'type': 'string'}" > your_file.py

    Exception :any:`JsonSchemaException` is thrown when validation fails.
    """
    _, code_generator = _factory(definition, handlers)
    return (
        'VERSION = "' + VERSION + '"\n' +
        code_generator.global_state_code + '\n' +
        code_generator.func_code
    )


def _factory(definition, handlers):
    resolver = RefResolver.from_schema(definition, handlers=handlers)
    code_generator = _get_code_generator_class(definition)(definition, resolver=resolver)
    return resolver, code_generator


def _get_code_generator_class(schema):
    # Schema in from draft-06 can be just the boolean value.
    if isinstance(schema, dict):
        schema_version = schema.get('$schema', '')
        if 'draft-04' in schema_version:
            return CodeGeneratorDraft04
        if 'draft-06' in schema_version:
            return CodeGeneratorDraft06
    return CodeGeneratorDraft07
