# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from nagare import presentation


class CardExtension(object):
    component_category = 'card-extension'

    def __init__(self, card):
        self.card = card

    def delete(self):
        pass


@presentation.render_for(CardExtension)
@presentation.render_for(CardExtension, 'cover')
# @presentation.render_for(CardExtension, 'edit')
@presentation.render_for(CardExtension, 'badge')
@presentation.render_for(CardExtension, 'header')
@presentation.render_for(CardExtension, 'action')
def render(*args):
    return ''
