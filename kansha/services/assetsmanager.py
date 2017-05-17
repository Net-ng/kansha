# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--
from paste import fileapp
from webob.exc import WSGIHTTPException

from nagare import presentation

from kansha.exceptions import NotFound
from .services_repository import Service


class AssetsManager(Service):
    LOAD_PRIORITY = 10
    CONFIG_SPEC = {
            'basedir': 'string',
            'max_size': 'integer(default=2048)',   # Max file size in kilobytes
            'baseurl': 'string'
        }

    THUMB_SIZE = (68, 68)
    MEDIUM_WIDTH = 425
    COVER_SIZE = (MEDIUM_WIDTH, 250)

    def copy(self, file_id):
        '''Copy a file from its file_id

        In:
            - ``file_id`` -- file id of the source file
        Return:
            - copied file id'''

    def save(self, data, file_id=None, metadata={}):
        """Save data, metadata and return an id

        In:
            - ``data`` -- data file
            - ``file_id`` -- file id, if None create an random id
            - ``metadata`` -- metdata of file (dict format)
        Return:
            - the file_id
        """
        pass

    def delete(self, file_id):
        '''Delete a file'''
        pass

    def load(self, file_id):
        """return data and metadata

        In:
            - ``file_id`` -- file identifier
        Return:
            - a tuple (data, metadata)
        """
        pass

    def update_metadata(self, file_id, metadata):
        """Update metadata of the file

        In:
            - ``file_id`` -- file identifier
            - ``metadata`` -- new metadata
        """
        pass

    def get_metadata(self, file_id):
        """Return metadata of the file

        Return:
            - metadata (dict format)
        """
        pass

    def data_for_src(self, file_id):
        """Return data for attribute src of img tag

        In:
            - ``file_id`` -- file identifier
        Return:
            - src attribute of image tag
        """
        data, metadata = self.load(file_id, True)
        return "data:image/gif;base64,%s" % data.encode('base64')


@presentation.init_for(AssetsManager, "len(url) >= 2")
def init_assets(self, url, comp, http_method, request):
    try:
        metadata = self.get_metadata(url[0])
    except IOError:
        raise NotFound()

    content_type = metadata.get('content-type')
    headers = {'content-type': content_type} if content_type else {}

    raise FileResponse(self._get_filename(url[0],
                                          url[1] if len(url) > 1 else None),
                       **headers)


class FileResponse(WSGIHTTPException):

    def __init__(self, file_path, **headers):
        self._file_path = file_path
        self._headers = headers

    def __call__(self, environ, start_response):
        app = fileapp.FileApp(self._file_path,
                              allowed_methods=('GET', ),
                              cache_control='private, must-revalidate',
                              **self._headers)
        return app(environ, start_response)
