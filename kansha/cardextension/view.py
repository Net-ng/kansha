#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation
from .comp import CardExtension


@presentation.render_for(CardExtension)
@presentation.render_for(CardExtension, 'cover')
@presentation.render_for(CardExtension, 'badge')
@presentation.render_for(CardExtension, 'header')
@presentation.render_for(CardExtension, 'action')
def render(*args):
    return ''
