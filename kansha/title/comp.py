# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from nagare import component

from kansha import validator


class Title(object):
    def __init__(self, title, class_='title', height=None, placeholder=''):
        self.title = title
        self.class_ = class_
        self.height = height
        self.placeholder = placeholder

    def set_title(self, comp, title):
        text = title() and title().strip()
        if text:
            text = validator.clean_text(text)
            comp.answer(text)


class EditableTitle(component.Task):
    def __init__(self, title, cls=Title, *args, **kw):
        self.title = component.Component(cls(title, *args, **kw))

    def set_title(self, title):
        self.title().title = title

    def go(self, comp):
        while True:
            comp.call(self.title)
            new_title = comp.call(self.title, model='edit')
            if new_title is not None:
                comp.answer(new_title)
