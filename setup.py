#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

# https://packaging.python.org/en/latest/single_source_version.html
try:
    execfile('fastjsonschema/version.py')
except NameError:
    exec(open('fastjsonschema/version.py').read())


setup(
    name='fastjsonschema',
    version=VERSION,
    packages=['fastjsonschema'],

    install_requires=[
        'requests',
    ],
    extras_require={
        'devel': [
            'colorama',
            'jsonschema',
            'json-spec',
            'pylint',
            'pytest',
            'pytest-cache',
            'validictory',
        ],
    },

    url='https://github.com/seznam/python-fastjsonschema',
    author='Michal Horejsek',
    author_email='horejsekmichal@gmail.com',
    description='Fastest Python implementation of JSON schema',
    license='BSD',

    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
