# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from kansha import duration


def create_pipe(app, *args, **kw):
    app = duration.DurationWSGIMiddleware(app)
    return app
