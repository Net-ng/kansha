# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import unittest

from kansha.services.search import schema, sqliteengine, elasticengine

#TODO: test all types on schema, doc creation and search

class MyDocument(schema.Document):
    title = schema.Text(stored=True)
    tags = schema.Text(stored=False)
    pages = schema.Int(stored=True)
    description = schema.Text
    price = schema.Float(stored=True, indexed=False)


class Person(schema.Document):
    firstname = schema.Keyword(stored=True)
    lastname = schema.Keyword(stored=True)
    height = schema.Float
    weight = schema.Float
    age = schema.Int(stored=True, indexed=False)


class TestSchema(unittest.TestCase):

    def setUp(self):

        self.Doc = MyDocument

    def test_class_attributes(self):
        self.assertIsInstance(self.Doc.title, schema.Text)
        self.assertEqual(self.Doc.price.indexed, False)
        self.assertIsInstance(self.Doc.description, schema.Text)
        self.assertEqual(self.Doc.title.schema, self.Doc)
        self.assertEqual(self.Doc.pages.name, 'pages')

    def test_instance_default_attributes(self):
        doc = self.Doc(1)
        self.assertEqual(
            doc.title, schema.Text.default, u'default was not set')
        self.assertEqual(doc.pages, schema.Int.default, u'default was not set')

    def test_instance_attributes(self):
        doc = self.Doc('docid', title=u'Titre', tags=u'mot livre français',
                       pages=89, description=u'Description', price=5.6)
        self.assertEqual(doc.title, u'Titre', u'attribute not set')
        self.assertEqual(doc.tags, u'mot livre français', u'attribute not set')
        self.assertEqual(doc.pages, 89, u'attribute not set')
        self.assertEqual(doc.description, u'Description', u'attribute not set')
        self.assertEqual(doc.price, 5.6, u'attribute not set')


class TestImpSchema(TestSchema):

    def setUp(self):
        TestDocument = schema.Schema('MyDocument')
        TestDocument.add_field(schema.Text('title', stored=True))
        TestDocument.add_field(schema.Text('tags', stored=False))
        TestDocument.add_field(schema.Int('pages', stored=True))
        TestDocument.add_field(schema.Text('description'))
        TestDocument.add_field(schema.Float('price', stored=True, indexed=False))
        self.Doc = TestDocument


class TestImpSchemaAltSyntax(TestSchema):

    def setUp(self):
        TestDocument = (
            schema.Schema('MyDocument') +
            schema.Text('title', stored=True) +
            schema.Text('tags', stored=False) +
            schema.Int('pages', stored=True) +
            schema.Text('description') +
            schema.Float('price', stored=True, indexed=False)
        )
        self.Doc = TestDocument


class TestImpSchemaConstructor(TestSchema):

    def setUp(self):
        TestDocument = schema.Schema(
            'MyDocument',
            schema.Text('title', stored=True),
            schema.Text('tags', stored=False),
            schema.Int('pages', stored=True),
            schema.Text('description'),
            schema.Float('price', stored=True, indexed=False)
        )
        self.Doc = TestDocument


class IndexCursor(object):

    def __init__(self, testcase):
        self.testcase = testcase
        self.schema = ''
        self.docid = 0
        self.fields = {}
        self.operation = ''

    def insert(self, schema_name, docid, **fields):
        self._action('insert', schema_name, docid, fields)

    def update(self, schema_name, docid, **fields):
        self._action('update', schema_name, docid, fields)

    def _action(self, operation, schema_name, docid, fields):
        self.schema = schema_name
        self.docid = docid
        self.fields = fields
        self.operation = operation

    def assert_match(self, operation, document):
        self.testcase.assertEqual(operation, self.operation)
        self.testcase.assertEqual(document.schema_name, self.schema)
        self.testcase.assertEqual(document._id, self.docid)
        for name, value in self.fields.iteritems():
            self.testcase.assertEqual(getattr(document, name), value)


class TestIndexableAPI(unittest.TestCase):

    def setUp(self):
        TestDocument = (
            schema.Schema('MyDocument') +
            schema.Text('title', stored=True) +
            schema.Text('tags', stored=False) +
            schema.Int('pages', stored=True) +
            schema.Text('description') +
            schema.Float('price', stored=True, indexed=False)
        )
        self.doc = TestDocument('docid', title=u'Titre', tags=u'mot livre français',
                       pages=89, description=u'Description', price=5.6)

    def test_insert(self):
        cursor = IndexCursor(self)
        self.doc.save(cursor)
        cursor.assert_match('insert', self.doc)

    def test_update(self):
        cursor = IndexCursor(self)
        self.doc.save(cursor, update=True)
        cursor.assert_match('update', self.doc)


class SearchTestCase(object):

    collection = u'test'

    def _create_search_engine(self):
        raise NotImplementedError()

    def setUp(self):
        self.engine = self._create_search_engine()
        self.engine.create_collection([MyDocument, Person])
        self.MyDocument = MyDocument
        self.Person = Person

    def tearDown(self):
        self.engine.delete_collection()

    def load_documents(self):
        '''helper function'''
        doc1 = self.MyDocument(
            'doc1', title=u'Titre', tags=u'Un livre français best seller',
            pages=89, description=u'Description de qualité, avec des services.', price=10.0)
        doc2 = self.MyDocument(
            'doc2', title=u'Unit tests', tags=u'quality software',
            pages=89, description=u'Best practices and services.', price=9.90)
        doc3 = self.Person(
            'p1', firstname=u'John', lastname=u'Doe', height=180,
            weight=80.5, age=40)
        doc4 = self.Person(
            'p2', firstname=u'Joan', lastname=u'Watson', height=170,
            weight=60, age=42)
        self.engine.add_document(doc1)
        self.engine.add_document(doc2)
        self.engine.add_document(doc3)
        self.engine.add_document(doc4)
        self.engine.commit(sync=True)

    def test_add_document(self):
        self.load_documents()

    def test_remove_document(self):
        self.load_documents()
        self.engine.delete_document(self.MyDocument, 'doc1')
        self.engine.commit(sync=True)
        query = self.MyDocument.match(u'best')
        res = self.engine.search(query)
        self.assertEqual(len(res), 1)

    def test_update_document(self):
        self.load_documents()
        doc = self.MyDocument.delta('doc1', title=u'Titre augmenté')
        self.engine.update_document(doc)
        self.engine.commit(sync=True)
        query = self.MyDocument.match(u'augmenté')
        res = self.engine.search(query)
        self.assertEqual(len(res), 1)
        assert(res[0][1].title == u'Titre augmenté'
               and res[0][1].price == 10.0)

    def test_match_all(self):
        self.load_documents()
        query = self.MyDocument.match(u'best')
        res = self.engine.search(query)
        self.assertEqual(len(res), 2)
        query = self.MyDocument.match(u'tests')
        res = self.engine.search(query)
        self.assertEqual(res[0][1]._id, 'doc2')
        self.assertEqual(res[0][1].title, u'Unit tests')
        self.assertIsNone(res[0][1].tags)  # not stored

    def test_match_field(self):
        self.load_documents()
        query = self.MyDocument.tags.match(u'best')
        res = self.engine.search(query)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][1].title, u'Titre')

    def test_equal_field(self):
        self.load_documents()
        res = self.engine.search(self.MyDocument.pages == 89)
        self.assertEqual(len(res), 2)
        res = self.engine.search(self.Person.lastname == u'Doe')
        self.assertEqual(len(res), 1)

    def test_unindexed_field(self):
        '''Would fails on SQLite for operators other than match'''
        self.load_documents()
        res = self.engine.search(self.Person.age == 40)
        if not isinstance(self.engine, sqliteengine.SQLiteFTSEngine):
            self.assertEqual(len(res), 0)  # age not indexed

    def test_partial_match(self):
        self.load_documents()
        res = self.engine.search(self.MyDocument.match(u'qualit'))
        self.assertEqual(len(res), 2)

    def test_disjonction(self):
        '''Fails on SQLite if both use match'''
        self.load_documents()
        query = (self.MyDocument.pages == 89) | self.MyDocument.description.match(
            u'practices')
        res = self.engine.search(query)
        self.assertEqual(len(res), 2)

    def test_disjonction_fail(self):
        self.assertRaises(AssertionError, lambda: (
            self.MyDocument.pages == 89) | self.Person.firstname.match(u'John'))

    def test_multiterm(self):
        '''All terms must be present'''
        self.load_documents()
        query = self.MyDocument.match(u'quality services')
        res = self.engine.search(query)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][1]._id, 'doc2')
        query = self.MyDocument.match(u'quality description')
        res = self.engine.search(query)
        self.assertEqual(len(res), 0)

    def test_special_chars(self):
        self.load_documents()
        query = self.MyDocument.match('"best')
        res = self.engine.search(query)
        self.assertEqual(len(res), 2)


class ImpSchemaSearchTestCase(SearchTestCase):

    def setUp(self):
        MyDocument_ = schema.Schema('MyDocument')
        MyDocument_.add_field(schema.Text('title', stored=True))
        MyDocument_.add_field(schema.Text('tags', stored=False))
        MyDocument_.add_field(schema.Int('pages', stored=True))
        MyDocument_.add_field(schema.Text('description'))
        MyDocument_.add_field(schema.Float('price', stored=True, indexed=False))

        Person_ = schema.Schema('Person')
        Person_.add_field(schema.Keyword('firstname', stored=True))
        Person_.add_field(schema.Keyword('lastname', stored=True))
        Person_.add_field(schema.Float('height'))
        Person_.add_field(schema.Float('weight'))
        Person_.add_field(schema.Int('age', stored=True, indexed=False))

        self.engine = self._create_search_engine()
        self.engine.create_collection([MyDocument_, Person_])
        self.MyDocument = MyDocument_
        self.Person = Person_


class TestSQLiteEngine(SearchTestCase, unittest.TestCase):

    def _create_search_engine(self):
        return sqliteengine.SQLiteFTSEngine(self.collection, u'/tmp')


class TestElasticEngine(SearchTestCase, unittest.TestCase):

    def _create_search_engine(self):
        try:
            return elasticengine.ElasticSearchEngine(self.collection)
        except ValueError as exc:
            self.skipTest(unicode(exc))


class TestSQLiteEngineImpSchema(ImpSchemaSearchTestCase, unittest.TestCase):

    def _create_search_engine(self):
        return sqliteengine.SQLiteFTSEngine(self.collection, u'/tmp')


class TestElasticEngineImpSchema(ImpSchemaSearchTestCase, unittest.TestCase):

    def _create_search_engine(self):
        try:
            return elasticengine.ElasticSearchEngine(self.collection)
        except ValueError as exc:
            self.skipTest(unicode(exc))
