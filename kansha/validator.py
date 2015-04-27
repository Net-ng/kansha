# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from lxml import etree
from lxml.html import clean


def clean_text(text):
    cc = clean.Cleaner()
    text = cc.clean_html(text)
    text = etree.fromstring(text).text
    return text
