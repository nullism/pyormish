#!/usr/bin/env python
from distutils.core import setup

setup(name='pyormish',
    version = '0.8',
    description = 'A simple, ultra-lightweight ORM for MySQL, SQLite, and Postgres',
    author = 'Aaron Meier',
    author_email = 'webgovernor@gmail.com',
    packages = ['pyormish'],
    package_dir={'pyormish':'src/pyormish'},
    url = 'http://www.python.org/community/sigs/current/distutils-sig/'
)
