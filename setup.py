#!/usr/bin/env python
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open(os.path.join(os.path.dirname(__file__), "README.rst")) as readme:
    long_description = readme.read()

setup(
    name='fastjsonschema',
    version='1.6',
    packages=['fastjsonschema'],

    install_requires=[
        'requests',
    ],
    extras_require={
        "test": [
            "colorama",
            "jsonschema",
            "json-spec",
            "pytest",
            "validictory",
        ],
    },

    url='https://github.com/seznam/python-fastjsonschema',
    author='Michal Horejsek',
    author_email='horejsekmichal@gmail.com',
    description='Fastest Python implementation of JSON schema',
    long_description=long_description,
    license='BSD',

    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
