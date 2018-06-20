# Fast JSON schema for Python

This project was made to come up with fast JSON validations. See
documentation https://seznam.github.io/python-fastjsonschema/ for
performance test details.

Current version is implementation of [json-schema](http://json-schema.org/) draft-04. Note that there are some differences compared to JSON schema standard:

 * Regular expressions are full Python ones, not only what JSON schema
    allows. It's easier to allow everything and also it's faster to
    compile without limits. So keep in mind that when you will use more advanced regular expression, it may not work with other library.
 * JSON schema says you can use keyword ``default`` for providing default
    values. This implementation uses that and always returns transformed
    input data.

## Install

`pip install fastjsonschema`

Support for Python 3.3 and higher.

## Documentation

Documentation: https://seznam.github.io/python-fastjsonschema/
