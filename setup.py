#!/usr/bin/env python
from setuptools import setup, find_packages

# Changed according to debug-toolbar to be able to run tests in a sane way,
# with no external libraries (e.g. py.test, nose), and not using Django's
# canonical way (which is fine for projects but not for apps to be distributed):
# ./manage.py test

setup(
    name='Splango',
    version='0.2',
    description='Split (A/B) testing library for Django',
    author='Shimon Rura',
    author_email='shimon@rura.org',
    url='http://github.com/shimon/Splango',
    packages=find_packages(exclude=('tests', 'example')),
    package_data={'django-splango': ['templates/*.html', 'templates/*/*.html']},
    tests_require=[
        'django>=1.4,<1.6',
    ],
    test_suite='runtests.runtests',
)
