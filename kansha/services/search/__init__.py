#-*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
'''
Plugin based Seach Engine abstraction.
Available plugins are registered as entry points in distribution.
'''

# TODO: create plugins for whoosh, elasticsearch and solr

import pkg_resources


def SearchEngine(engine='dummy', **config):
    entry = pkg_resources.load_entry_point(
        'kansha', 'search.engines', engine)
    return entry(**config)
