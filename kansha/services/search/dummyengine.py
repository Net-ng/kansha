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
This engine does nothing but it works (i.e. it does not break)
It is here for documentation purpose.
For a basic effective engine, see SQLiteFTSEngine.
"""


class DummySearchEngine(object):

    # Make it compatible with services
    LOAD_PRIORITY = 30

    def __init__(self, index):
        self.index = index

    def add_document(self, document):
        '''
        Add a document to the data store, in index (a.k.a. collection)
        `index`, under the document type (a.k.a. schema) `schema`.
        The document is a `schema.Document` instance.
        '''
        pass

    def delete_document(self, schema, docid):
        '''
        Remove document from index and storage.
        schema is a `Document` class or Schema object.
        '''
        pass

    def update_document(self, document):
        '''Update document'''
        pass

    def commit(self, sync=False):
        '''
        Validate add/upgrade/delete operations since last commit.
        The ``sync`` option controls whether the operation is
        synchronous or not (default to False) if backend supports it.
        '''
        pass

    def cancel(self):
        '''
        Forget documents added since last commit'''
        pass

    def search(self, query, size=20):
        '''
        Search the database.
        The query Query expression (see search.query).
        Return list of tuples (score, document).
        The returned document only contains stored values, the others
        are set to None.
        '''
        return []

    def create_collection(self, schemas):
        '''
        Init the collections the first time.
        Just use once! Or you'll have to reindex all your documents.
        `schemas` is a list of Document classes or Schema instances.
        '''
        pass

    def delete_collection(self):
        pass
