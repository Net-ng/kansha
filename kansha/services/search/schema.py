#-*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
"""
Schemas are used to define Documents.
Example usage:

class MyDoc(Document):
    title = TEXT(stored=True)
    created = DATETIME
    description = TEXT

doc = MyDoc(1001, title=u'Programming Python')
The first argument is a mandatory, arbitrary id.

"""

# TODO
# type checking, linguistic settings (language, collations, stop words,
# lexers, ...)

from datetime import datetime
from .query import *


class FieldType(object):

    parent = None
    name = ''

    def __init__(self, indexed=True, stored=False, default=None):
        self.indexed = indexed
        self.stored = stored
        if default is not None:
            self.default = default

    def __eq__(self, v):
        return EQQuery(self, v)

    def __ne__(self, v):
        return NEQuery(self, v)

    def __gt__(self, v):
        return GTQuery(self, v)

    def __ge__(self, v):
        return GTEQuery(self, v)

    def __lt__(self, v):
        return LTQuery(self, v)

    def __le__(self, v):
        return LTEQuery(self, v)

    def in_(self, v):
        return INQuery(self, v)

    def match(self, v):
        return MATCHQuery(self, v)

    def match_phrase(self, v):
        return PHRASEQuery(self, v)


class TEXT(FieldType):

    '''Fulltext field'''
    default = u''


class KEYWORD(FieldType):

    '''Exact match string'''
    default = u''


class ATTACHMENT(FieldType):

    '''
    File, as a file path unicode string, whose content
    is to be indexed.
    '''
    default = None


class NUMBER(FieldType):
    pass


class FLOAT(NUMBER):
    default = 0.0


class INT(NUMBER):
    default = 0


class BOOLEAN(FieldType):
    default = True


class DATETIME(FieldType):
    default = datetime.now()


class _DocType(type):

    def __new__(cls, name, bases, dct):
        fields = {}
        for aname, aval in dct.items():
            if isinstance(aval, FieldType):
                aval.name = aname
                fields[aname] = aval
            elif isinstance(aval, type) and issubclass(aval, FieldType):
                val = aval()
                val.name = aname
                fields[aname] = dct[aname] = val
        klass = super(_DocType, cls).__new__(cls, name, bases, dct)
        klass.fields = fields
        for v in fields.itervalues():
            v.parent = klass
        return klass


class Document(object):

    '''
    Declarative class for documents.

    The `fields` and `match` attributes are reserved: don't declare properties with those names!
    '''

    __metaclass__ = _DocType

    def __init__(self, docid, **fields):
        '''
        Instanciate new document.
        The caller is responsible for giving a (preferably) unique id to the document.
        The id is not part of the schema declaration and is mandatory.
        it can be used to track the document's origin for example.
        Fields values not specified to the constructor are set to their defaults.
        Fields set to None are ignored (that is, in case of update,
        they are left untouched in the index).
        '''
        self._id = docid
        for fname, fvalue in self.fields.iteritems():
            setattr(self, fname, fields.get(fname, fvalue.default))

    @classmethod
    def delta(cls, docid, **fields):
        '''
        Alternate constructor to build delta documents.
        Fields values not specified to the constructor are set to None.
        '''
        for fname in cls.fields:
            if fname not in fields:
                fields[fname] = None
        return cls(docid, **fields)

    @classmethod
    def match(cls, v):
        '''Full text specific: match any of the fields'''
        return MATCHANYQuery(cls, v)
