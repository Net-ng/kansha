# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--


class AssetsManager(object):

    def __init__(self):
        """Init method
        """
        pass

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
