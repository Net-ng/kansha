# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import pkg_resources
import unittest

from kansha.services.dummyassetsmanager import dummyassetsmanager
from kansha.services.simpleassetsmanager import simpleassetsmanager


class DummyAssetsManagerTest(unittest.TestCase):

    def setUp(self):
        self.dam = dummyassetsmanager.DummyAssetsManager()

    def test_load(self):
        """DummyAssetsManagerTest - Test load"""
        package = pkg_resources.Requirement.parse('kansha')
        fname = pkg_resources.resource_filename(
            package, 'kansha/services/dummyassetsmanager/tie.jpg')
        with open(fname, 'r') as f:
            data = f.read()

        res_data, res_metadata = self.dam.load('mock_id')
        self.assertEqual(res_data, data)
        self.assertEqual(res_metadata, {})

    def test_save(self):
        """DummyAssetsManagerTest - Test save"""
        package = pkg_resources.Requirement.parse('kansha')
        fname = pkg_resources.resource_filename(
            package, 'kansha/services/dummyassetsmanager/tie.jpg')
        with open(fname, 'r') as f:
            data = f.read()

        file_id = self.dam.save(data, {})
        self.assertEqual(file_id, 'mock_id')


class SimpleAssetsManagerTest(unittest.TestCase):

    def setUp(self):
        self.dam = simpleassetsmanager.SimpleAssetsManager(
            '/tmp', 'kansha', max_size=2048)

    def test_save_and_load(self):
        """SimpleAssetsManagerTest - Test save and load #1, save and load an image with metadata"""
        package = pkg_resources.Requirement.parse('kansha')
        test_file = pkg_resources.resource_filename(
            package, 'kansha/services/dummyassetsmanager/tie.jpg')
        with open(test_file, 'r') as f:
            data = f.read()

        file_id = self.dam.save(
            data, metadata={"id": "tie.jpg", "creation_date": "2013/01/02"})

        res_data, res_metadata = self.dam.load(file_id)
        self.assertEqual(res_data, data)
        self.assertEqual(
            res_metadata, {"id": "tie.jpg", "creation_date": "2013/01/02"})

    def test_save_and_load_2(self):
        """SimpleAssetsManagerTest - Test save and load #2, save and load an image without metadata"""
        package = pkg_resources.Requirement.parse('kansha')
        test_file = pkg_resources.resource_filename(
            package, 'kansha/services/dummyassetsmanager/tie.jpg')
        with open(test_file, 'r') as f:
            data = f.read()

        file_id = self.dam.save(data)

        res_data, res_metadata = self.dam.load(file_id)
        self.assertEqual(res_data, data)
        self.assertEqual(res_metadata, {})

    def test_save_and_load_3(self):
        """SimpleAssetsManagerTest - Test save and load #3, save and load an image with given id"""
        package = pkg_resources.Requirement.parse('kansha')
        test_file = pkg_resources.resource_filename(
            package, 'kansha/services/dummyassetsmanager/tie.jpg')
        with open(test_file, 'r') as f:
            data = f.read()

        file_id = self.dam.save(data, file_id="test.jpg")
        self.assertEqual(file_id, "test.jpg")
        res_data, _ = self.dam.load("test.jpg")
        self.assertEqual(res_data, data)
