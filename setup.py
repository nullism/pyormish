#!/usr/bin/env python
from distutils.core import setup
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__),'src'))
from pyormish import __version__

setup(name='pyormish',
    version = __version__,
    description = 'A simple, ultra-lightweight ORM for MySQL, SQLite, and Postgres',
    author = 'Aaron Meier',
    author_email = 'webgovernor@gmail.com',
    packages = ['pyormish'],
    package_dir={'pyormish':'src/pyormish'},
    url = 'http://www.python.org/community/sigs/current/distutils-sig/'
)
