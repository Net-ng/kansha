# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import random
import json

import webob.exc

from nagare import presentation
from nagare.ajax import YUI_PREFIX


class Autocomplete(object):

    """
    Enhance an existing field by providing an auto-completion feature.

    Parameters:
      - ``field_id``: the field (input or textarea) that should be enhanced
      - ``completion_func``: a function that returns the completion suggestions
        for a given query: it could be a collection of name strings or a
        collection of (name, markup) pairs; the markup is shown in the
        drop-down list (or the name when markup is not available) and the name
        is inserted in the field when the item is selected
      - ``delimiter``: specify the delimiter used if the field is multi-valued
    """

    def __init__(self, field_id, completion_func, delimiter=None,
                 min_query_length=3, max_results_displayed=20):
        self.field_id = field_id
        self.completion_func = completion_func
        self.delimiter = delimiter
        self.min_query_length = int(min_query_length)
        self.max_results_displayed = int(max_results_displayed)
        self.var = 'autocomplete' + str(random.randint(10000000, 99999999))

    def _completion_results(self, query, static_url):
        def make_pair(item):
            if hasattr(item, '__iter__'):
                return item
            else:
                return item, item

        results = self.completion_func(query, static_url)
        return [make_pair(item) for item in results]


def json_response(data):
    """Create a JSON response from the data"""
    return webob.exc.HTTPOk(body=json.dumps(data),
                            content_type='application/json')


@presentation.render_for(Autocomplete, model='static_dependencies')
def render_static_dependencies(self, h, comp, *args):
    # Unused for now...
    for mod in ('autocomplete',):
        h.head.css_url(YUI_PREFIX +
                       '/%(mod)s/assets/skins/sam/%(mod)s.css' % dict(mod=mod))

    h.head.javascript_url(YUI_PREFIX + '/yahoo-dom-event/yahoo-dom-event.js')
    for mod in ('connection', 'animation', 'json',
                'datasource', 'autocomplete'):
        h.head.javascript_url(
            YUI_PREFIX + '/%(mod)s/%(mod)s-min.js' % dict(mod=mod))
    h.head.javascript_url('js/autocomplete.js')
    return h.root


@presentation.render_for(Autocomplete)
def render_autocomplete(self, h, comp, *args):

    static_url = h.head.static_url

    def get_results(query):
        raise json_response(self._completion_results(query, static_url))

    callback_id = h.register_callback(1, get_results, False)
    completion_url = h.add_sessionid_in_url(params=('_a', '%s=' % callback_id))

    subst = dict(
        var=self.var,
        field_id=json.dumps(self.field_id),
        completion_url=json.dumps(completion_url),
        delimiter=json.dumps(self.delimiter),
        min_query_length=self.min_query_length,
        max_results_displayed=self.max_results_displayed,
    )
    js = ('var %(var)s = YAHOO.kansha.autocomplete.init(%(field_id)s,'
          ' %(completion_url)s, %(delimiter)s, %(min_query_length)s, '
          '%(max_results_displayed)s);' % subst)
    h << h.script(js, type='text/javascript')

    return h.root
