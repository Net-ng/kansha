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
    title = Text(stored=True)
    created = Datetime
    description = Text

doc = MyDoc(1001, title=u'Programming Python')
The first argument is a mandatory, arbitrary id.

"""

# TODO
# type checking, linguistic settings (language, collations, stop words,
# lexers, ...)

from datetime import datetime
from .query import *


class FieldType(object):

    schema = None

    def __init__(self, name='', indexed=True, stored=False, default=None):
        self.name = name
        self.indexed = indexed
        self.stored = stored
        if default is not None:
            self.default = default

    @property
    def type_name(self):
        return self.__class__.__name__

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

    def map(self, schema_name, mapper):
        mapper.define_field(
            schema_name,
            self.type_name,
            self.name,
            self.indexed,
            self.stored
        )


class Text(FieldType):

    '''Fulltext field'''
    default = u''


class Keyword(FieldType):

    '''Exact match string'''
    default = u''


class Attachment(FieldType):

    '''
    File, as a file path unicode string, whose content
    is to be indexed.
    '''
    default = None


class Number(FieldType):
    pass


class Float(Number):
    default = 0.0


class Int(Number):
    default = 0


class Boolean(FieldType):
    default = True


class Datetime(FieldType):
    default = datetime.now()


class IndexableDocument(object):
    '''Document Type for documents instanciated by a Schema object.'''

    def __init__(self, schema, fields, docid, **field_values):
        self._id = docid
        self.fields = fields
        self.schema = schema
        for name, field in fields.iteritems():
            setattr(self, name, field_values.get(name, field.default))

    @property
    def schema_name(self):
        return self.schema.type_name

    def save(self, cursor, update=False):
        fields = dict(
            (name, getattr(self, name)) for name in self.fields
            if getattr(self, name) is not None
        )
        if update:
            cursor.update(self.schema_name, docid=self._id, **fields)
        else:
            cursor.insert(self.schema_name, docid=self._id, **fields)


class _Schema(type):
    """
    Meta-class
    """

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
        klass = super(_Schema, cls).__new__(cls, name, bases, dct)
        klass.fields = fields
        klass.type_name = name
        for v in fields.itervalues():
            v.schema = klass
        return klass


class Document(IndexableDocument):

    '''
    Declarative class for documents.

    The `fields`, 'delta' , 'type_name', 'schema' and `match` attributes are reserved: don't declare properties with those names!

    Usage:

        class MyDocument(schema.Document):
            title = schema.Text(stored=True)
            tags = schema.Text(stored=False)
            pages = schema.Int(stored=True)
            description = schema.Text
            price = schema.Float(stored=True, indexed=False)

        doc1 = MyDocument(
                    'doc1', title=u'Titre', tags=u'Un livre français best seller',
                    pages=89, description=u'Description de qualité, avec des services.', price=10.0)
        query = MyDocument.match(u'tests')
        query = MyDocument.tags.match(u'best')
        query = (MyDocument.pages == 89) | MyDocument.description.match(
                    u'practices')

    '''

    __metaclass__ = _Schema

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
    def schema(self):
        return self.__class__

    @property
    def schema_name(self):
        return self.__class__.type_name

    @classmethod
    def delta(cls, docid, **fields):
        '''
        Alternate constructor to build delta documents.
        Fields values not specified to the constructor are set to None.
        '''
        for fname in set(cls.fields) - set(fields):
            fields[fname] = None
        return cls(docid, **fields)

    @classmethod
    def match(cls, v):
        '''Full text specific: match any of the fields'''
        return MATCHANYQuery(cls, v)

    @classmethod
    def map(cls, mapper):
        mapper.define(cls.type_name)
        for field in cls.fields.itervalues():
            field.map(cls.type_name, mapper)

    @classmethod
    def iter_fields(cls):
        return cls.fields.iteritems()


class Schema(object):
    '''Imperatively build a Document schema.

    Same reserved keywords as the Declarative Schema.

    Usage:

        TestDocument = schema.Schema(
            'MyDocument',
            schema.Text('title', stored=True),
            schema.Text('tags', stored=False),
            schema.Int('pages', stored=True),
            schema.Text('description'),
            schema.Float('price', stored=True, indexed=False)
        )

    or

        # Incrementaly update schema "in place"
        TestDocument = schema.Schema('MyDocument')
        TestDocument.add_field(schema.Text('title', stored=True))
        TestDocument.add_field(schema.Text('tags', stored=False))
        TestDocument.add_field(schema.Int('pages', stored=True))
        TestDocument.add_field(schema.Text('description'))
        TestDocument.add_field(schema.Float('price', stored=True, indexed=False))

    or create new schema from existing one

        TestDocument2 = TestDocument + schema.Text('author')
        TestDocument2.type_name = 'IdentifiedDocument'

    TestDocument is then used as if it was a Declarative Document schema.
    '''

    def __init__(self, name, *fields):
        self.type_name = name
        self.fields = {}
        for field in fields:
            self.add_field(field)

    def add_field(self, field):
        """Update schema in place."""
        assert(field.name)
        assert(field.name != 'schema')
        assert(not hasattr(self, field.name))
        field.schema = self
        self.fields[field.name] = field

    def __add__(self, field):
        """Create a new augmented schema."""
        new_schema = Schema(self.type_name, *self.fields.values())
        new_schema.add_field(field)
        return new_schema

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
        return IndexableDocument(self, self.fields, docid, **fields)

    def delta(self, docid, **fields):
        '''
        Alternate constructor to build delta documents.
        Fields values not specified to the constructor are set to None.
        '''
        for fname in set(self.fields) - set(fields):
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

    def __getstate__(self):
        return (self.type_name, self.fields)

    def __setstate__(self, data):
        self.type_name, self.fields = data

    def map(self, mapper):
        mapper.define(self.type_name)
        for field in self.fields.itervalues():
            field.map(self.type_name, mapper)

    def iter_fields(self):
        return self.fields.iteritems()
