# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2015 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from setuptools import setup, find_packages
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

with open(path.join(here, 'VERSION.txt'), encoding='utf-8') as f:
    version = f.read().strip()

setup(
    name='kansha',
    version=version,
    author='',
    author_email='',
    description='Manage and share collaborative pinboards on the web.',
    long_description=long_description,
    license='BSD',
    keywords='',
    url='',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['*.cfg', '*.ini']},
    zip_safe=False,
    install_requires=(
        'PEAK-Rules==0.5a1.dev-r2713',
        'nagare[database,i18n]', 'docutils', 'Pillow', 'pycrypto', 'Babel',
        'requests', 'oauth2', 'SQLAlchemy==0.9.8', 'dateutils', 'xlwt',
        'Paste==1.7.5.1'
    ),
    extras_require={'test': ('nose',),
                    'debug': ('WebError',),
                    'ldap': ('python-ldap',),
                    'mysql': ('oursql',),
                    'elastic': ('elasticsearch',)},
    message_extractors={'kansha': [('**.py', 'python', None)]},
    entry_points="""
      [nagare.applications]
      kansha = kansha.app:app
      [nagare.commands]
      create-index = kansha.batch.create_index:ReIndex
      [search.engines]
      dummy = kansha.services.search.dummyengine:DummySearchEngine
      sqlite = kansha.services.search.sqliteengine:SQLiteFTSEngine
      elastic = kansha.services.search.elasticengine:ElasticSearchEngine
      """
)
