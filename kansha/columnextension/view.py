#--
# Copyright (c) 2012-2017 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation

from .comp import ColumnExtension


@presentation.render_for(ColumnExtension, 'header')
def render(*args):
    return ''
