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

class SQLiteFTSMapper(object):

    def match(self, field, value):
        query = '%s match ?' % field.name
        # sqlite does not analyse, do it ourselves
        return (query, (unialpha.sub(u' ', value) + u'*',))

    def matchany(self, doctype, value):
        query = '%s match ?' % doctype.__name__
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


class SQLiteFTSEngine(object):

    '''
    Basic search engine, weakly typed, every field is indexed.
    Sufficient in most cases.
    '''

    def __init__(self, index, index_folder):
        assert(index.isalnum())
        self.init_state(index, index_folder)

    def init_state(self, collection, index_folder):
        self.collection = collection
        self.index_folder = index_folder
        self.connection = sqlite3.connect(
            os.path.join(index_folder, collection + '.fts'))
        self._cursor = None
        self.mapper = SQLiteFTSMapper()

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
        `collection`, under the document type (a.k.a. schema) `doctype`.

        '''
        c = self._get_cursor()
        # neither doctype nor fields keys are user inputs, so this is safe
        query_base = ('insert into %s(id,%s) values (%s)' %
                      (document.__class__.__name__,
                       ','.join(document.fields.keys()),
                       ','.join(('?',) * (len(document.fields) + 1))
                       )
                      )
        params = [document._id] + [getattr(document, field)
                                   for field in document.fields.iterkeys()]
        c.execute(query_base, params)

    def delete_document(self, doctype, docid):
        '''
        Remove document from index and storage.
        '''
        c = self._get_cursor()
        c.execute('delete from %s where id=?' % doctype.__name__, (docid,))

    def update_document(self, document):
        '''Update document'''
        params = []
        qset = []
        for f in document.fields:
            v = getattr(document, f)
            if v is not None:
                qset.append("%s = ?" % f)
                params.append(v)
        query = 'update %s set %s where id=?' % (
            document.__class__.__name__, ', '.join(qset))
        params.append(document._id)
        c = self._get_cursor()
        c.execute(query, params)

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
        where, params = query(self.mapper)
        doctype = query.queried_doc
        c = self._get_cursor()
        sql = 'select id as docid, %s from %s where %s limit %s' % (
            ', '.join(f.name for f in doctype.fields.itervalues()
                      if f.stored),
            doctype.__name__, where, size
        )
        c.execute(sql, params)
        fields = [d[0].lower() for d in c.description]
        # no score function in sqlite, so every result is given weight 1
        l = [(1, doctype.delta(**dict(zip(fields, row))))
             for row in c.fetchall()]
        return l

    def delete_collection(self):
        self._dropdb()

    def create_collection(self, schema):
        '''
        Init the collections the first time.
        Just use once! Or you'll have to reindex all your documents.
        Schema is a list of Document classes.
        '''
        c = self._get_cursor()
        for doctype in schema:
            # no type declaration on FTS tables, so we ignore
            # doctype.fields.values
            c.execute('drop table if exists %s' % doctype.__name__)
            notindexed = ['notindexed=id']
            for fname, field in doctype.fields.iteritems():
                if not field.indexed:
                    notindexed.append("notindexed=" + fname)
            slversion = sqlite3.sqlite_version_info[:3]
            if slversion > (3, 8, 0):
                c.execute(
                    '''CREATE VIRTUAL TABLE %s USING fts4(id, %s, prefix="3,5,7", %s);''' %
                    (doctype.__name__,
                     ','.join(doctype.fields.keys()),
                     ','.join(notindexed))
                )
            elif slversion > (3, 7, 7):
                print "Warning: older version of sqlite3 detected, please upgrade to sqlite 3.8.0 or newer."
                c.execute(
                    '''CREATE VIRTUAL TABLE %s USING fts4(id, %s, prefix="3,5,7");''' %
                    (doctype.__name__,
                     ','.join(doctype.fields.keys()))
                )
            else:
                raise ImportError('Your version of sqlite3 is too old, please upgrade to sqlite 3.8.0 or newer.')
        self.commit()
