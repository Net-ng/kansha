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
    title = schema.TEXT(stored=True)
    tags = schema.TEXT(stored=False)
    pages = schema.INT(stored=True)
    description = schema.TEXT
    price = schema.FLOAT(stored=True, indexed=False)


class Person(schema.Document):
    firstname = schema.KEYWORD(stored=True)
    lastname = schema.KEYWORD(stored=True)
    height = schema.FLOAT
    weight = schema.FLOAT
    age = schema.INT(stored=True, indexed=False)


class TestSchema(unittest.TestCase):

    def setUp(self):

        self.Doc = MyDocument

    def test_class_attributes(self):
        self.assertIsInstance(self.Doc.title, schema.TEXT)
        self.assertEqual(self.Doc.price.indexed, False)
        self.assertIsInstance(self.Doc.description, schema.TEXT)
        self.assertEqual(self.Doc.title.parent, MyDocument)
        self.assertEqual(self.Doc.pages.name, 'pages')

    def test_instance_default_attributes(self):
        doc = self.Doc(1)
        self.assertEqual(
            doc.title, schema.TEXT.default, u'default was not set')
        self.assertEqual(doc.pages, schema.INT.default, u'default was not set')

    def test_instance_attributes(self):
        doc = self.Doc('docid', title=u'Titre', tags=u'mot livre français',
                       pages=89, description=u'Description', price=5.6)
        self.assertEqual(doc.title, u'Titre', u'attribute not set')
        self.assertEqual(doc.tags, u'mot livre français', u'attribute not set')
        self.assertEqual(doc.pages, 89, u'attribute not set')
        self.assertEqual(doc.description, u'Description', u'attribute not set')
        self.assertEqual(doc.price, 5.6, u'attribute not set')


class SearchTestCase(object):

    collection = u'test'

    def _create_search_engine(self):
        raise NotImplementedError()

    def setUp(self):
        self.engine = self._create_search_engine()
        self.engine.create_collection([MyDocument, Person])

    def tearDown(self):
        self.engine.delete_collection()

    def load_documents(self):
        '''helper function'''
        doc1 = MyDocument(
            'doc1', title=u'Titre', tags=u'Un livre français best seller',
            pages=89, description=u'Description de qualité, avec des services.', price=10.0)
        doc2 = MyDocument(
            'doc2', title=u'Unit tests', tags=u'quality software',
            pages=89, description=u'Best practices and services.', price=9.90)
        doc3 = Person(
            'p1', firstname=u'John', lastname=u'Doe', height=180,
            weight=80.5, age=40)
        doc4 = Person(
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
        self.engine.delete_document(MyDocument, 'doc1')
        self.engine.commit(sync=True)
        query = MyDocument.match(u'best')
        res = self.engine.search(query)
        self.assertEqual(len(res), 1)

    def test_update_document(self):
        self.load_documents()
        doc = MyDocument.delta('doc1', title=u'Titre augmenté')
        self.engine.update_document(doc)
        self.engine.commit(sync=True)
        query = MyDocument.match(u'augmenté')
        res = self.engine.search(query)
        self.assertEqual(len(res), 1)
        assert(res[0][1].title == u'Titre augmenté'
               and res[0][1].price == 10.0)

    def test_match_all(self):
        self.load_documents()
        query = MyDocument.match(u'best')
        res = self.engine.search(query)
        self.assertEqual(len(res), 2)
        query = MyDocument.match(u'tests')
        res = self.engine.search(query)
        self.assertEqual(res[0][1]._id, 'doc2')
        self.assertEqual(res[0][1].title, u'Unit tests')
        self.assertIsNone(res[0][1].tags)  # not stored

    def test_match_field(self):
        self.load_documents()
        query = MyDocument.tags.match(u'best')
        res = self.engine.search(query)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][1].title, u'Titre')

    def test_equal_field(self):
        self.load_documents()
        res = self.engine.search(MyDocument.pages == 89)
        self.assertEqual(len(res), 2)
        res = self.engine.search(Person.lastname == u'Doe')
        self.assertEqual(len(res), 1)

    def test_unindexed_field(self):
        '''Would fails on SQLite for operators other than match'''
        self.load_documents()
        res = self.engine.search(Person.age == 40)
        if not isinstance(self.engine, sqliteengine.SQLiteFTSEngine):
            self.assertEqual(len(res), 0)  # age not indexed

    def test_partial_match(self):
        self.load_documents()
        res = self.engine.search(MyDocument.match(u'qualit'))
        self.assertEqual(len(res), 2)

    def test_disjonction(self):
        '''Fails on SQLite if both use match'''
        self.load_documents()
        query = (MyDocument.pages == 89) | MyDocument.description.match(
            u'practices')
        res = self.engine.search(query)
        self.assertEqual(len(res), 2)

    def test_disjonction_fail(self):
        self.assertRaises(AssertionError, lambda: (
            MyDocument.pages == 89) | Person.firstname.match(u'John'))

    def test_multiterm(self):
        '''All terms must be present'''
        self.load_documents()
        query = MyDocument.match(u'quality services')
        res = self.engine.search(query)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][1]._id, 'doc2')
        query = MyDocument.match(u'quality description')
        res = self.engine.search(query)
        self.assertEqual(len(res), 0)

    def test_special_chars(self):
        self.load_documents()
        query = MyDocument.match('"best')
        res = self.engine.search(query)
        self.assertEqual(len(res), 2)


class TestSQLiteEngine(SearchTestCase, unittest.TestCase):

    def _create_search_engine(self):
        return sqliteengine.SQLiteFTSEngine(self.collection, u'/tmp')


class TestElasticEngine(SearchTestCase, unittest.TestCase):

    def _create_search_engine(self):
        try:
            return elasticengine.ElasticSearchEngine(self.collection)
        except ValueError as exc:
            self.skipTest(unicode(exc))
