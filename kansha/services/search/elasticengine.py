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


class ESQueryMapper(object):

    def match(self, field, value):
        return {'match': {field.name: {'query': value, 'operator': 'and'}}}

    def matchany(self, schema, value):
        # _all does not make sense for fulltext searches
        # so we use a custom field for that: _full.
        # it only contains Text fields
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


class ESSchemaMapper(object):

    FT2ES = {
        'Text': {'type': 'string',
                 'analyzer':  'autocomplete',
                 'search_analyzer': 'standard',
                 'copy_to': '_full'},
        'Keyword': {'type': 'string',
                    'index': 'not_analyzed'},
        'Attachment': {'type': 'attachment'},
        'Float': {'type': 'double'},
        'Int': {'type': 'long'},
        'Boolean': {'type': 'boolean'},
        'Datetime': {'type': 'date'}
    }

    SETTINGS = {
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

    def __init__(self, idx_manager):

        self.idx_manager = idx_manager
        self.mappings = {}

    # Schema API

    def define(self, schema_name):
        properties = {'_full': {"type": "string",
                                "analyzer":  "autocomplete",
                                "search_analyzer": "standard"}}
        excludes = []
        self.mappings[schema_name] = {'properties': properties,
                                      '_source': {"excludes": excludes}}

    def define_field(self, schema_name, field_type, name, indexed, stored):
        estype = dict(self.FT2ES[field_type])
        if not indexed:
            estype['index'] = 'no'
        mapping = self.mappings[schema_name]
        mapping['properties'][name] = estype
        if not stored:
            mapping['_source']['excludes'].append(name)

    ## Specific API

    def create(self, index):
        body = {"mappings": self.mappings, "settings": self.SETTINGS}
        self.idx_manager.create(index=index, body=body)


class IndexCursor(object):

    def __init__(self, index, search_function=None):
        self.index = index
        self.es_search = search_function
        self.op = {}

    # Document API

    def insert(self, schema_name, docid, **fields):
        self._action(schema_name, docid, fields)

    def update(self, schema_name, docid, **fields):
        self._action(schema_name, docid, fields, update=True)

    # Query API

    def search(self, schema_name, fields_to_load, mapped_query, limit):
        """
        ``fields_to_load`` is  a list of field names.
        """
        dsl = mapped_query
        self.op = dict(index=self.index,
                       doc_type=schema_name,
                       body={'query': dsl},
                       size=limit)

    def get_results(self, result_factory):
        hits = self.es_search(**self.op)
        return [
            (h['_score'], result_factory(h['_id'], **h['_source']))
            for h in hits['hits']['hits']
        ]

    # Specific API

    def _action(self, schema_name, docid, fields, update=False):
        doc = 'doc' if update else '_source'
        self.op = {
            '_index': self.index,
            '_type': schema_name,
            '_op_type': 'update' if update else 'create',
            '_id': docid,
            doc: fields
        }

    def enqueue(self, queue):
        queue.append(self.op)


class ElasticSearchEngine(object):
    '''
    ElasticSearch Engine.
    '''

    # make it compatible with services
    LOAD_PRIORITY = 30

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
        self.mapper = ESQueryMapper()

    # be persistence friendly
    def __getstate__(self):
        return (self.index, self.host, self.port)

    def __setstate__(self, state):
        self.init_state(*state)

    def _index(self, document, update=False):
        # for efficiency, nothing is executed yet,
        # we prepare and queue the operation
        cursor = IndexCursor(self.index)
        document.save(cursor, update)
        cursor.enqueue(self._queue)

    def add_document(self, document):
        '''
        Add a document to the data store, in index (a.k.a. collection),
        under the document type.
        '''
        self._index(document)

    def delete_document(self, schema, docid):
        '''
        Remove document from index and storage.
        '''
        op = {
            '_op_type': 'delete',
            '_index': self.index,
            '_type': schema.type_name,
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
        index_cursor = IndexCursor(self.index, self.es.search)
        return query.search(index_cursor, self.mapper, size)

    def delete_collection(self):
        if self.idx_manager.exists(self.index):
            self.idx_manager.delete(index=self.index)

    def create_collection(self, schemas):
        '''
        Init the collections the first time.
        Just use once! Or you'll have to reindex all your documents.
        `schemas` is a list of Document classes or Schema instances.
        '''

        idx_manager = self.idx_manager
        if idx_manager.exists(self.index):
            idx_manager.delete(index=self.index)

        mapper = ESSchemaMapper(idx_manager)
        for schema in schemas:
            schema.map(mapper)

        mapper.create(self.index)
