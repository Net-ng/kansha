# -*- coding:utf-8 -*-
# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import re
import unicodedata
from cStringIO import StringIO

import xlwt
from webob import exc
from nagare.i18n import _
from peak.rules import when

from kansha.cardextension import CardExtension


def get_extension_title(card_extension_class):
    '''Return a title (string) if the extension has to write something in Excel export, None otherwise'''


def write_extension_data(card_extension, worksheet, row, col, style):
    '''Write data to Excel sheet'''


def get_extension_title_for(cls):
    cond = 'card_extension_class.__name__ == "%s"' % cls.__name__
    return when(get_extension_title, cond)


def write_extension_data_for(cls):
    cond = 'isinstance(card_extension, %s)' % cls.__name__
    return when(write_extension_data, cond)


@when(get_extension_title, CardExtension)
def get_extension_title_CardExtension(card_extension):
    return None


@when(write_extension_data, CardExtension)
def write_extension_data_CardExtension(card_extension):
    pass


class ExcelExport(object):
    def __init__(self, board):
        self.board = board
        self.workbook = xlwt.Workbook()
        name = unicodedata.normalize('NFKD', self.board.get_title()).encode('ascii', 'ignore')
        self.filename = re.sub('\W+', '_', name.lower())
        self.sheet_name = re.sub('\W+', ' ', name)[:31]
        self.extensions = []
        self.extension_titles = []
        for name, cls in self.board.card_extensions.iteritems():
            title = get_extension_title(cls)
            if title is not None:
                self.extensions.append(name)
                self.extension_titles.append(title)

    def write(self):
        sty = ''
        header_sty = xlwt.easyxf(sty + 'font: bold on; align: wrap on, vert centre, horiz center;')
        sty = xlwt.easyxf(sty)
        ws = self.workbook.add_sheet(self.sheet_name)

        titles = [_(u'Column'), _(u'Title')] + self.extension_titles
        for col, title in enumerate(titles):
            ws.write(0, col, title, style=header_sty)

        row = 1
        for column in self.board.columns:
            column = column()
            colname = _('Archived cards') if column.is_archive else column.get_title()
            for card in column.cards:
                card = card()
                ws.write(row, 0, colname, sty)
                ws.write(row, 1, card.get_title(), sty)
                card_extensions = dict(card.extensions)
                for col, key in enumerate(self.extensions, 2):
                    ext = card_extensions[key]()
                    write_extension_data(ext, ws, row, col, sty)
                row += 1
        for col in xrange(len(titles)):
            ws.col(col).width = 0x3000
        ws.set_panes_frozen(True)
        ws.set_horz_split_pos(1)

    def download(self):
        buffer = StringIO()
        self.write()
        self.workbook.save(buffer)
        buffer.seek(0)
        e = exc.HTTPOk()
        e.content_type = 'application/vnd.ms-excel'
        e.content_disposition = u'attachment;filename=%s.xls' % self.filename
        e.body = buffer.getvalue()
        raise e
