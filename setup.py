#!/usr/bin/env python
"""
Copyright (c) 2012, Aaron Meier
All rights reserved.

See LICENSE for more information.
"""
from distutils.core import setup
import os
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__),'src'))
from pyormish import __version__

setup(name='pyormish',
    version = __version__,
    description = 'A simple, ultra-lightweight ORM for MySQL, SQLite, and Postgres',
    long_description = (
        "PyORMish is an ORM (ish) thing designed to provide quick and easy OO data access "
        "without all the mumbo jumbo of a traditional ORM. "
    ),
    author = 'Aaron Meier',
    author_email = 'webgovernor@gmail.com',
    packages = ['pyormish'],
    package_dir={'pyormish':'src/pyormish'},
    package_data={'pyormish':['examples/*.py']},
    url = 'http://pyormish.nullism.com',
    license = 'BSD'
)
