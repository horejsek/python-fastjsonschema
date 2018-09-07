===========================
Fast JSON schema for Python
===========================

|PyPI| |Pythons|

.. |PyPI| image:: https://img.shields.io/pypi/v/fastjsonschema.svg
   :alt: PyPI version
   :target: https://pypi.python.org/pypi/fastjsonschema

.. |Pythons| image:: https://img.shields.io/pypi/pyversions/fastjsonschema.svg
   :alt: Supported Python versions
   :target: https://pypi.python.org/pypi/fastjsonschema

This project was made to come up with fast JSON validations. It is at
least an order of magnitude faster than other Python implemantaions.
See `documentation <https://horejsek.github.io/python-fastjsonschema/>`_ for
performance test details.

This library follows and implements `JSON schema draft-04, draft-06 and draft-07
<http://json-schema.org>`_. Note that there are some differences compared to JSON
schema standard:

 * Regular expressions are full Python ones, not only what JSON schema allows. It's easier
   to allow everything and also it's faster to compile without limits. So keep in mind that when
   you will use more advanced regular expression, it may not work with other library or in
   other language.
 * JSON schema says you can use keyword ``default`` for providing default values. This implementation
   uses that and always returns transformed input data.

Install
-------

.. code-block:: bash

    pip install fastjsonschema

Support only for Python 3.3 and higher.

Documentation
-------------

Documentation: `https://horejsek.github.io/python-fastjsonschema<https://horejsek.github.io/python-fastjsonschema>`_
