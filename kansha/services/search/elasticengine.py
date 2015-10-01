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
ElasticSearch based search engine plugin.
Depends on a running ElasticSearch cluster, somewhere.
For usage, look at the unit tests.
"""

try:
    from elasticsearch import Elasticsearch, helpers
    from elasticsearch.client import IndicesClient
except ImportError:
    es_installed = False
else:
    es_installed = True

from . import schema


class ESMapper(object):

    def match(self, field, value):
        return {'match': {field.name: {'query': value, 'operator': 'and'}}}

    def matchany(self, doctype, value):
        # _all does not make sense for fulltext searches
        # so we use a custom field for that: _full.
        # it only contains TEXT fields
        return {'match': {'_full': {'query': value, 'operator': 'and'}}}

    def eq(self, field, value):
        return {'term': {field.name: value}}

    def gt(self, field, value):
        return {
            'range': {
                field.name: {'gt': value}
            }
        }

    def gte(self, field, value):
        return {
            'range': {
                field.name: {'gte': value}
            }
        }

    def lt(self, field, value):
        return {
            'range': {
                field.name: {'lt': value}
            }
        }

    def lte(self, field, value):
        return {
            'range': {
                field.name: {'lte': value}
            }
        }

    def in_(self, field, value):
        return {'terms': {field.name: value}}

    def and_(self, exp1, exp2):
        return {
            'bool': {
                'must': [exp1, exp2]
            }
        }

    def or_(self, exp1, exp2):
        return {
            'bool': {
                'should': [exp1, exp2]
            }
        }

FT2ES = {
    schema.TEXT: {'type': 'string',
                  "index_analyzer":  "autocomplete",
                  "search_analyzer": "standard",
                  'copy_to': '_full'},
    schema.KEYWORD: {'type': 'string',
                     'index': 'not_analyzed'},
    schema.ATTACHMENT: {'type': 'attachment'},
    schema.FLOAT: {'type': 'double'},
    schema.INT: {'type': 'long'},
    schema.BOOLEAN: {'type': 'boolean'},
    schema.DATETIME: {'type': 'date'}
}


def ESProperty(ftype):
    estype = dict(FT2ES[ftype.__class__])
    if not ftype.indexed:
        estype['index'] = 'no'
    # ElasticSearch stores all the document by default, so we can ignore the
    # stored attribute of field types here.
    return estype


class ElasticSearchEngine(object):
    '''
    ElasticSearch Engine.
    '''

    def __init__(self, index, host=None, port=None):
        '''Only one host for now.'''
        if not es_installed:
            raise ValueError('elasticsearch not installed')

        assert(index.isalpha())
        self.init_state(index, host, port)

    def init_state(self, index, host, port):
        self._queue = []
        self.index = index
        self.host = host
        self.port = port
        if host is None:
            self.es = Elasticsearch()
        else:
            self.es = Elasticsearch(hosts=[{'host': host, 'port': port}])
        self.idx_manager = IndicesClient(self.es)
        self.mapper = ESMapper()

    # be persistence friendly
    def __getstate__(self):
        return (self.index, self.host, self.port)

    def __setstate__(self, state):
        self.init_state(*state)

    def _index(self, document, update=False):
        # for efficiency, nothing is executed yet,
        # we prepare and queue the operation
        doc = 'doc' if update else '_source'
        op = {
            '_index': self.index,
            '_type': document.__class__.__name__,
            '_op_type': 'update' if update else 'create',
            '_id': document._id,
            doc: {k: getattr(document, k)
                  for k in document.fields
                  if getattr(document, k) is not None}
        }
        self._queue.append(op)

    def add_document(self, document):
        '''
        Add a document to the data store, in index (a.k.a. collection),
        under the document type.
        '''
        self._index(document)

    def delete_document(self, doctype, docid):
        '''
        Remove document from index and storage.
        '''
        op = {
            '_op_type': 'delete',
            '_index': self.index,
            '_type': doctype.__name__,
            '_id': docid
        }
        self._queue.append(op)

    def update_document(self, document):
        '''Update document (partial update from delta document)'''
        self._index(document, True)

    def commit(self, sync=False):
        '''
        If ``sync``, index synchronously, else let Elasticsearch
        manage its index.
        '''
        helpers.bulk(self.es, self._queue)
        if sync:
            self.idx_manager.refresh(self.index)
        self._queue = []

    def cancel(self):
        '''
        Forget operation scheduled since last commit'''
        self._queue = []

    def search(self, query, size=20):
        '''
        Search the database.
        '''
        dsl = query(self.mapper)
        hits = self.es.search(index=self.index,
                              doc_type=query.queried_doc.__name__,
                              body={'query': dsl},
                              size=size)
        res = [
            (h['_score'], query.queried_doc.delta(h['_id'],
                                                  **h['_source']))
            for h in hits['hits']['hits']
        ]
        return res

    def delete_collection(self):
        if self.idx_manager.exists(self.index):
            self.idx_manager.delete(index=self.index)

    def create_collection(self, schema):
        '''
        Init the collections the first time.
        Just use once! Or you'll have to reindex all your documents.
        Schema is a list of Document classes.
        '''

        idx_manager = self.idx_manager
        if idx_manager.exists(self.index):
            idx_manager.delete(index=self.index)

        mappings = {}
        for doctype in schema:
            properties = {'_full': {"type": "string",
                                    "index_analyzer":  "autocomplete",
                                    "search_analyzer": "standard"}}
            excludes = []
            for name, ftype in doctype.fields.iteritems():
                properties[name] = ESProperty(ftype)
                if not ftype.stored:
                    excludes.append(name)
            mappings[doctype.__name__] = {'properties': properties,
                                          '_source': {"excludes": excludes}}
        settings = {
            "number_of_shards": 1,
            "analysis": {
                "filter": {
                    "autocomplete_filter": {
                        "type":     "ngram",
                        "min_gram": 1,
                        "max_gram": 20
                    }
                },
                "analyzer": {
                    "autocomplete": {
                        "type":      "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "autocomplete_filter"
                        ]
                    }
                }
            }
        }
        body = {"mappings": mappings, "settings": settings}
        idx_manager.create(index=self.index, body=body)
