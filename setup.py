#!/usr/bin/env python
import os
from setuptools import setup, find_packages

# Changed according to debug-toolbar to be able to run tests in a sane way,
# with no external libraries (e.g. py.test, nose), and not using Django's
# canonical way (which is fine for projects but not for apps to be distributed):
# ./manage.py test

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-splango',
    version='0.21',
    packages=find_packages(exclude=('tests', 'example')),
    include_package_data=True,
    description='Split (A/B) testing library for Django',
    url='http://github.com/shimon/Splango',
    author='Shimon Rura',
    author_email='shimon@rura.org',
    install_requires=[
        'django>=1.4,<1.6',
        'django-cache-machine==0.8'
    ],
    tests_require=[
        'django>=1.4,<1.6',
        'django-cache-machine==0.8',
        'mock==1.0.1',
        'selenium==2.31.0'
    ],
    test_suite='runtests.runtests'
)
