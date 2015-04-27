# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import ajax, serializer
import peak


class ActionViewToJs(ajax.ViewToJs):

    def __init__(self, output):
        self.output = output


@peak.rules.when(ajax.serialize_body, (ActionViewToJs,))
def serialize_body(view_to_js, content_type, doctype):
    return view_to_js.output


@peak.rules.when(serializer.serialize, (ActionViewToJs,))
def serialize(self, content_type, doctype, declaration):
    return ('text/plain', self.output)


class Action(ajax.Update):

    def __init__(self, action):
        # The ``action`` function will be called on the server
        # with a renderer parameter if ``with_renderer=True`
        # else without any parameter.
        #
        # It can return a javascript code which will be executed
        # on the client.
        super(Action, self).__init__(render=action, component_to_update='')

    @classmethod
    def _generate_response(cls, render, args, js, component_to_update, r):
        return ActionViewToJs(cls.generate_javascript(render, args))

    @classmethod
    def generate_javascript(cls, render, args):
        return render(*args)


class Actions(Action):

    def __init__(self, *actions):
        super(Actions, self).__init__(lambda: actions, True)

    def generate_javascript(self, h):
        return ';'.join(action.generate_javascript(h) for action in self.render())
