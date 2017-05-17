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
SQLite FTS based search engine plugin.
Zero dependency.
For usage, look at the unit tests.
"""

import sqlite3
import os.path
import re

unialpha = re.compile('[\W_]+', re.UNICODE)


class SQLiteFTSQueryMapper(object):

    def match(self, field, value):
        query = '%s match ?' % field.name
        # sqlite does not analyse, do it ourselves
        return (query, (unialpha.sub(u' ', value) + u'*',))

    def matchany(self, schema, value):
        query = '%s match ?' % schema.type_name
        return (query, (unialpha.sub(u' ', value) + u'*',))

    def eq(self, field, value):
        query = '%s = ?' % field.name
        return (query, (value,))

    def gt(self, field, value):
        query = '%s > ?' % field.name
        return (query, (value,))

    def gte(self, field, value):
        query = '%s >= ?' % field.name
        return (query, (value,))

    def lt(self, field, value):
        query = '%s < ?' % field.name
        return (query, (value,))

    def lte(self, field, value):
        query = '%s <= ?' % field.name
        return (query, (value,))

    def in_(self, field, value):
        query = '%s in (%s)' % (field.name,
                                ','.join(('?',) * len(value)))
        return (query, value)

# FTS does not behave like normal SQL for match operations.
# TODO: rewrite accordingly

    def and_(self, exp1, exp2):
        query = '(%s and %s)' % (exp1[0], exp2[0])
        params = exp1[1] + exp2[1]
        return (query, params)

    def or_(self, exp1, exp2):
        query = '(%s or %s)' % (exp1[0], exp2[0])
        params = exp1[1] + exp2[1]
        return (query, params)


class SQLiteFTSSchemaMapper(object):

    def __init__(self, db_cursor):
        self.db_cursor = db_cursor
        self.mappings = {}

    # Schema API

    def define(self, schema_name):
        self.mappings[schema_name] = {
            'notindexed': ['notindexed=id'],
            'fields': []
        }

    def define_field(self, schema_name, field_type, name, indexed, stored):
        # SQLite fts tables are not typed, ignoring field_type
        # SQLite fts always stores, ignoring stored.
        mapping = self.mappings[schema_name]
        if not indexed:
            mapping['notindexed'].append("notindexed=" + name)
        mapping['fields'].append(name)

    # specific API

    def create(self):
        for schema_name, mapping in self.mappings.iteritems():
            self.db_cursor.execute('drop table if exists %s' % schema_name)
            slversion = sqlite3.sqlite_version_info[:3]
            if slversion > (3, 8, 0):
                self.db_cursor.execute(
                    '''CREATE VIRTUAL TABLE %s USING fts4(id, %s, prefix="3,5,7", %s);''' %
                    (schema_name,
                     ','.join(mapping['fields']),
                     ','.join(mapping['notindexed']))
                )
            elif slversion > (3, 7, 7):
                print "Warning: older version of sqlite3 detected, please upgrade to sqlite 3.8.0 or newer."
                self.db_cursor.execute(
                    '''CREATE VIRTUAL TABLE %s USING fts4(id, %s, prefix="3,5,7");''' %
                    (schema_name,
                     ','.join(mapping['fields']))
                )
            else:
                raise ImportError('Your version of sqlite3 is too old, please upgrade to sqlite 3.8.0 or newer.')


class IndexCursor(object):

    def __init__(self,  db_cursor):
        self.db_cursor = db_cursor
        self.query = ''
        self.params = []

    # Document API

    def insert(self, schema_name, docid, **fields):
        # neither schema nor fields keys are user inputs, so this is safe
        self.query = (
            'insert into %s(id,%s) values (%s)' %
            (
                schema_name,
                ','.join(fields.keys()),
                ','.join(('?',) * (len(fields) + 1))
            )
        )
        self.params = [docid] + [value for value in fields.itervalues()]

    def update(self, schema_name, docid, **fields):
        qset = []
        for name, value in fields.iteritems():
            qset.append("%s = ?" % name)
            self.params.append(value)
        self.query = 'update %s set %s where id=?' % (
            schema_name, ', '.join(qset))
        self.params.append(docid)

    # Query API

    def search(self, schema_name, fields_to_load, mapped_query, limit):
        """
        ``fields_to_load`` is  a list of field names.
        """
        where, params = mapped_query
        self.query = 'select id as docid, %s from %s where %s limit %s' % (
            ', '.join(field for field in fields_to_load),
            schema_name, where, limit
        )
        self.params = params

    def get_results(self, result_factory):
        self.execute()
        fields = [d[0].lower() for d in self.db_cursor.description]
        # no score function in sqlite, so every result is given weight 1
        scored_results = [(1, result_factory(**dict(zip(fields, row))))
             for row in self.db_cursor.fetchall()]
        return scored_results

    # Specific API

    def execute(self):
        self.db_cursor.execute(self.query, self.params)


class SQLiteFTSEngine(object):

    '''
    Basic search engine, weakly typed, every field is indexed.
    Sufficient in most cases.
    '''

    # make it compatible with services
    LOAD_PRIORITY = 30

    def __init__(self, index, index_folder):
        assert(index.isalnum())
        self.init_state(index, index_folder)

    def init_state(self, collection, index_folder):
        self.collection = collection
        self.index_folder = index_folder
        self.connection = sqlite3.connect(
            os.path.join(index_folder, collection + '.fts'))
        self._cursor = None
        self.mapper = SQLiteFTSQueryMapper()

    # be persistence friendly
    def __getstate__(self):
        return (self.collection, self.index_folder)

    def __setstate__(self, state):
        self.init_state(*state)

    def _get_cursor(self):
        if not self._cursor:
            self._cursor = self.connection.cursor()
        return self._cursor

    def _dropdb(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self._cursor = None
        db = os.path.join(self.index_folder, self.collection + '.fts')
        os.unlink(db)

    def add_document(self, document):
        '''
        Add a document to the data store, in collection (a.k.a. index)
        `collection`, under the document type (a.k.a. schema) `schema`.

        '''
        index_cursor = IndexCursor(self._get_cursor())
        document.save(index_cursor)
        index_cursor.execute()

    def delete_document(self, schema, docid):
        '''
        Remove document from index and storage.
        '''
        c = self._get_cursor()
        c.execute('delete from %s where id=?' % schema.type_name, (docid,))

    def update_document(self, document):
        '''Update document'''
        index_cursor = IndexCursor(self._get_cursor())
        document.save(index_cursor, update=True)
        index_cursor.execute()

    def commit(self, sync=False):
        '''``sync`` option is ignored by this engine'''
        if not self._cursor:
            # no operation in progress
            return
        self.connection.commit()
        self._cursor.close()
        self._cursor = None

    def cancel(self):
        '''
        Forget documents added since last commit'''
        if self._cursor:
            self._cursor.close()
            self._cursor = None

    def search(self, query, size=20):
        '''
        Search the database.
        '''
        index_cursor = IndexCursor(self._get_cursor())
        return query.search(index_cursor, self.mapper, size)

    def delete_collection(self):
        self._dropdb()

    def create_collection(self, schemas):
        '''
        Init the collections the first time.
        Just use once! Or you'll have to reindex all your documents.
        `schemas` is a list of Document classes or Schema instances.
        '''
        c = self._get_cursor()
        mapper = SQLiteFTSSchemaMapper(c)
        for schema in schemas:
            schema.map(mapper)
        mapper.create()
        self.commit()
