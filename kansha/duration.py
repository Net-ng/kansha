# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from __future__ import absolute_import

import functools
import time

from nagare import log


def _default_log(msg, duration):
    log.debug(msg, duration)


class DurationLogger(object):

    def __init__(self, msg=None, log_msg=None):
        self._msg = msg or 'duration: %0.3f'
        self._log = log_msg or _default_log

    def start(self):
        self._start_time = time.time()

    def stop(self):
        duration = time.time() - self._start_time
        self._log(self._msg, duration)

    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

duration_context = DurationLogger()


def log_duration(msg=None, log_msg=None):
    def decorator(f):
        @functools.wraps(f)
        def new_f(*args, **kw):
            with DurationLogger(msg, log_msg):
                return f(*args, **kw)
        return new_f
    return decorator


class DurationWSGIMiddleware:

    def __init__(self, app):
        self._app = app

    @log_duration('request took %0.3f')
    def __call__(self, environ, start_response):
        return self._app(environ, start_response)
