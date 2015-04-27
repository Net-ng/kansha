# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation
from paste import fileapp
from webob.exc import WSGIHTTPException
from .assetsmanager import AssetsManager


@presentation.init_for(AssetsManager, "len(url) >= 2")
def init_assets(self, url, comp, http_method, request):
    headers = {}
    metadata = self.get_metadata(url[0])
    try:
        headers['content_type'] = metadata['content-type']
    except KeyError:
        pass

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
