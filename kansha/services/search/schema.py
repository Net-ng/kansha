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

    def __init__(self, name='', indexed=True, stored=False, default=None):
        self.name = name
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
        klass.type_name = name
        for v in fields.itervalues():
            v.parent = klass
        return klass


class Document(object):

    '''
    Declarative class for documents.

    The `fields` and `match` attributes are reserved: don't declare properties with those names!
    '''

    __metaclass__ = _DocType

    type_name = 'Document'

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

    @property
    def doc_type(self):
        return self.__class__

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


class AltDocument(object):
    '''Document Type for documents instanciated by a Schema object.'''

    def __init__(self, schema, fields, docid, **field_values):
        self._id = docid
        self.fields = fields
        self.schema = schema
        for name, field in fields.iteritems():
            setattr(self, name, field_values.get(name, field.default))

    @property
    def doc_type(self):
        return self.schema


class Schema(object):
    '''Imperatively build a Document schema'''

    def __init__(self, name):
        self.type_name = name
        self.fields = {}

    def add_field(self, name, field):

        assert(name != 'doc_type')
        assert(not hasattr(self, name))
        if isinstance(field, FieldType):
            field.name = name
            field.parent = self
            self.fields[name] = field
        elif isinstance(field, type) and issubclass(field, FieldType):
            field_object = field()
            field_object.name = name
            field_object.parent = self
            self.fields[name] = field_object

    def __add__(self, field):
        """Alternate syntax. Requires named field instances."""
        assert(field.name)
        self.add_field(field.name, field)
        return self

    def __call__(self, docid, **fields):
        '''
        Document factory.
        Instanciate new document.
        The caller is responsible for giving a (preferably) unique id to the document.
        The id is not part of the schema declaration and is mandatory.
        it can be used to track the document's origin for example.
        Fields values not specified to the constructor are set to their defaults.
        Fields set to None are ignored (that is, in case of update,
        they are left untouched in the index).
        '''
        return AltDocument(self, self.fields, docid, **fields)

    def delta(self, docid, **fields):
        '''
        Alternate constructor to build delta documents.
        Fields values not specified to the constructor are set to None.
        '''
        for fname in self.fields:
            if fname not in fields:
                fields[fname] = None
        return self(docid, **fields)

    def match(self, v):
        '''Full text specific: match any of the fields'''
        return MATCHANYQuery(self, v)

    def __getattr__(self, name):
        try:
            return self.fields[name]
        except KeyError:
            raise AttributeError(name)
