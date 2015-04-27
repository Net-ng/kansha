# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
"""
Abstract Query expressions.
Queries are not tied to a search engine. They can be built independently, persisted and
then executed by any search engine.
Each search engine is responsible for interpreting queries at search time
by calling them with a mapper.

Search engines don't support joins, so you can query only one document type at once.

See unit tests for example usage.
"""


class Query(object):

    operation = 'nop'

    def __init__(self, field, value):
        self.field = field
        self.value = value
        self.queried_doc = self.field.parent

    def __call__(self, mapper):
        op = getattr(mapper, self.operation)
        return op(self.field, self.value)

    def __and__(self, other):
        return ANDQuery(self, other)

    def __or__(self, other):
        return ORQuery(self, other)


class EQQuery(Query):
    operation = 'eq'


class NEQuery(Query):
    operation = 'neq'


class GTQuery(Query):
    operation = 'gt'


class GTEQuery(Query):
    operation = 'gte'


class LTQuery(Query):
    operation = 'lt'


class LTEQuery(Query):
    operation = 'lte'


class MATCHQuery(Query):
    operation = 'match'


class MATCHANYQuery(Query):
    '''
    Match any field in the document.
    The first argument is not a field but a document
    '''
    operation = 'matchany'

    def __init__(self, doc, value):
        self.field = doc
        self.value = value
        self.queried_doc = doc


class PHRASEQuery(Query):
    operation = 'phrase'


class INQuery(Query):
    '''Passed value must be iterable'''
    operation = 'in_'


class ANDQuery(object):

    operation = 'and_'

    def __init__(self, q1, q2):
        assert(q1.queried_doc == q2.queried_doc)
        self.q1 = q1
        self.q2 = q2
        self.queried_doc = q1.queried_doc

    def __call__(self, mapper):
        op = getattr(mapper, self.operation)
        return op(self.q1(mapper), self.q2(mapper))

    def __and__(self, other):
        return ANDQuery(self, other)

    def __or__(self, other):
        return ORQuery(self, other)


class ORQuery(ANDQuery):

    operation = 'or_'
