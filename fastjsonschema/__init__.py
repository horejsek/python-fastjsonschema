"""
This project is there because commonly used JSON schema libraries in Python
are really slow which was problem at out project. Just let's see some numbers first:

 * Probalby most popular ``jsonschema`` can take in tests up to 11 seconds for valid inputs
   and 2.5 seconds for invalid inputs.
 * Secondly most popular ``json-spec`` is even worse with up to 12 and 3 seconds.
 * Lastly ``validictory`` is much better with 800 or 50 miliseconds, but it does not
   follow all standards and it can be still slow for some purposes.

That's why there is this project which compiles definition into Python most stupid code
which people would had hard time to write by themselfs because of not-written-rule DRY
(don't repeat yourself). When you compile definition, then times are 60 miliseconds for
valid inputs and 3 miliseconds for invalid inputs. Pretty amazing, right? :-)

You can try it for yourself with included script:

.. code-block:: bash

    $ make performance
    fast_compiled        valid      ==> 0.06058199889957905
    fast_compiled        invalid    ==> 0.0028909146785736084
    fast_not_compiled    valid      ==> 7.054106639698148
    fast_not_compiled    invalid    ==> 1.6773221027106047
    jsonschema           valid      ==> 11.189393147826195
    jsonschema           invalid    ==> 2.642645660787821
    jsonspec             valid      ==> 11.942349303513765
    jsonspec             invalid    ==> 2.9887414034456015
    validictory          valid      ==> 0.7500483158230782
    validictory          invalid    ==> 0.03606216423213482

This library follows and implements `JSON schema <http://json-schema.org>`_. Sometimes
it's not perfectly clear so I recommend also check out this `understaning json schema
<https://spacetelescope.github.io/understanding-json-schema>`_.

Note that there are some differences compared to JSON schema standard:

 * ``dependency`` for objects are not implemented yet. Future implementation will not change speed.
 * ``patternProperty`` for objects are not implemented yet. Future implementation can little bit
   slow down validation of object properties. Of course only for those who uses ``properties``.
 * ``definitions`` for sharing JSON schema are not implemented yet. Future implementation will
   not change speed.
 * Regular expressions are full what Python provides, not only what JSON schema allows. It's easier
   to allow everything and also it's faster to compile without limits. So keep in mind that when
   you will use more advanced regular expression, it may not work with other library.
 * JSON schema says you can use keyword ``default`` for providing default values. This implementation
   uses that and always returns transformed input data.

Support only for Python 3.3 and higher.
"""

from .exceptions import JsonSchemaException
from .generator import CodeGenerator

__all__ = ('JsonSchemaException', 'compile')


def compile(definition):
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

    Exception :any:`JsonSchemaException` is thrown when validation fails.
    """
    code_generator = CodeGenerator(definition)
    local_state = {}
    exec(code_generator.func_code, code_generator.global_state, local_state)
    return local_state['func']
