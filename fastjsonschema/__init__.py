#    ___
#    \./     DANGER: This project implements some code generation
# .--.O.--.          techniques involving string concatenation.
#  \/   \/           If you look at it, you might die.
#

r"""
Installation
************

.. code-block:: bash

    pip install fastjsonschema

Support only for Python 3.3 and higher.

About
*****

``fastjsonschema`` implements validation of JSON documents by JSON schema.
The library implements JSON schema drafts 04, 06 and 07. The main purpose is
to have a really fast implementation. See some numbers:

 * Probably most popular ``jsonschema`` can take up to 5 seconds for valid inputs
   and 1.2 seconds for invalid inputs.
 * Second most popular ``json-spec`` is even worse with up to 7.2 and 1.7 seconds.
 * Last ``validictory``, now deprecated, is much better with 370 or 23 milliseconds,
   but it does not follow all standards and it can be still slow for some purposes.

With this library you can gain big improvements as ``fastjsonschema`` takes
only about 25 milliseconds for valid inputs and 2 milliseconds for invalid ones.
Pretty amazing, right? :-)

Technically it works by generating the most stupid code on the fly which is fast but
is hard to write by hand. The best efficiency is achieved when compiled once and used
many times, of course. It works similarly like regular expressions. But you can also
generate the code to the file which is even slightly faster.

You can do the performance on your computer or server with an included script:

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

This library follows and implements `JSON schema draft-04, draft-06, and draft-07
<http://json-schema.org>`_. Sometimes it's not perfectly clear so I recommend also
check out this `understanding JSON schema <https://spacetelescope.github.io/understanding-json-schema>`_.

Note that there are some differences compared to JSON schema standard:

 * Regular expressions are full Python ones, not only what JSON schema allows. It's easier
   to allow everything and also it's faster to compile without limits. So keep in mind that when
   you will use a more advanced regular expression, it may not work with other library or in
   other languages.
 * Because Python matches new line for a dollar in regular expressions (``a$`` matches ``a`` and ``a\\n``),
   instead of ``$`` is used ``\Z`` and all dollars in your regular expression are changed to ``\\Z``
   as well. When you want to use dollar as regular character, you have to escape it (``\$``).
 * JSON schema says you can use keyword ``default`` for providing default values. This implementation
   uses that and always returns transformed input data.

API
***
"""

from .draft04 import CodeGeneratorDraft04
from .draft06 import CodeGeneratorDraft06
from .draft07 import CodeGeneratorDraft07
from .exceptions import JsonSchemaException, JsonSchemaDefinitionException
from .ref_resolver import RefResolver
from .version import VERSION

__all__ = ('VERSION', 'JsonSchemaException', 'JsonSchemaDefinitionException',
           'compile', 'compile_to_code', 'get_code_generator_class', 'validate')


def validate(definition, data, handlers: dict = None, formats: dict = None, **kwargs):
    """
    Validation function for lazy programmers or for use cases, when you need
    to call validation only once, so you do not have to compile it first.
    Use it only when you do not care about performance (even thought it will
    be still faster than alternative implementations).

    .. code-block:: python

        import fastjsonschema

        validate({'type': 'string'}, 'hello')
        # same as: compile({'type': 'string'})('hello')

    Preferred is to use :any:`compile` function.
    """
    return compile(definition, handlers, formats, **kwargs)(data)


# pylint: disable=redefined-builtin,exec-used
def compile(definition, handlers=None, formats=None, **kwargs):
    """
    Generates validation function for validating JSON schema passed in ``definition``.
    Example:

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

    Exception :any:`JsonSchemaDefinitionException` is raised when generating the
    code fails (bad definition).

    Exception :any:`JsonSchemaException` is raised from generated funtion when
    validation fails (data do not follow the definition).
    """
    resolver, code_generator = _factory(definition, handlers, formats, **kwargs)
    global_state = code_generator.global_state
    # Do not pass local state so it can recursively call itself.
    exec(code_generator.func_code, global_state)
    return global_state[resolver.get_scope_name()]


def compile_to_code(definition, handlers=None, formats=None, **kwargs):
    """
    Generates validation code for validating JSON schema passed in ``definition``.
    Example:

    .. code-block:: python

        import fastjsonschema

        code = fastjsonschema.compile_to_code({'type': 'string'})
        with open('your_file.py', 'w') as f:
            f.write(code)

    You can also use it as a script:

    .. code-block:: bash

        echo "{'type': 'string'}" | python3 -m fastjsonschema > your_file.py
        python3 -m fastjsonschema "{'type': 'string'}" > your_file.py

    Exception :any:`JsonSchemaDefinitionException` is raised when generating the
    code fails (bad definition).
    """
    _, code_generator = _factory(definition, handlers, formats, **kwargs)
    return (
        'VERSION = "' + VERSION + '"\n' +
        code_generator.global_state_code + '\n' +
        code_generator.func_code
    )


def _factory(definition, handlers=None, formats=None, **kwargs):
    resolver = kwargs.pop('resolver', None) or RefResolver.from_schema(definition, handlers=handlers or {})
    generator_class = get_code_generator_class(definition)
    code_generator = generator_class(definition, resolver=resolver, formats=formats or {}, **kwargs)
    return resolver, code_generator


def get_code_generator_class(schema):
    # Schema in from draft-06 can be just the boolean value.
    if isinstance(schema, dict):
        schema_version = schema.get('$schema', '')
        if 'draft-04' in schema_version:
            return CodeGeneratorDraft04
        if 'draft-06' in schema_version:
            return CodeGeneratorDraft06
    return CodeGeneratorDraft07


# backwards compatibality
# pylint: disable=invalid-name
_get_code_generator_class = get_code_generator_class
