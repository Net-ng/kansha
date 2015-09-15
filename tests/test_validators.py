# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import unittest

from kansha import validator


class ValidatorTest(unittest.TestCase):

    def test_boolean_validator(self):
        '''Test Boolean validator conversion type
        '''
        validate = validator.BoolValidator

        self.assertEqual(validate(True).value, True)
        self.assertEqual(validate(1).value, True)
        self.assertEqual(validate('true').value, True)
        self.assertEqual(validate('on').value, True)
        self.assertEqual(validate('yes').value, True)

        self.assertEqual(validate('test').value, False)
        self.assertEqual(validate(False).value, False)
        self.assertEqual(validate(0).value, False)
        self.assertEqual(validate('false').value, False)
        self.assertEqual(validate('off').value, False)
        self.assertEqual(validate('no').value, False)
