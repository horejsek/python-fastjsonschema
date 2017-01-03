#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name='fastjsonschema',
    version='1.1',
    packages=['fastjsonschema'],

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
