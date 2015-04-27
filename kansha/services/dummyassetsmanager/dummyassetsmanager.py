# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import log
import pkg_resources

from ..assetsmanager import AssetsManager


class DummyAssetsManager(AssetsManager):

    def save(self, data, file_id=None, metadata={}):
        log.debug("Save Image")
        log.debug("%s" % metadata)
        return 'mock_id'

    def load(self, file_id):
        log.debug("Load Image")
        package = pkg_resources.Requirement.parse('kansha')
        fname = pkg_resources.resource_filename(package, 'kansha/services/dummyassetsmanager/tie.jpg')
        with open(fname, 'r') as f:
            data = f.read()
        return data, {}

    def update_metadata(self, file_id, metadata):
        pass

    def get_metadata(self, file_id):
        pass
