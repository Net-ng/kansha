# --
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import json
import random

from nagare import component, database, i18n, security

from kansha import notifications
from kansha import title
from kansha.cardextension import CardExtension

from .models import DataChecklist, DataChecklistItem


class NewChecklistItem(object):

    def __init__(self):
        self.focus = False


class ChecklistItem(object):

    def __init__(self, id_, data=None):
        self.id = id_
        data = data if data is not None else self.data
        self.title = component.Component(
            title.EditableTitle(
                self.get_title,
                placeholder=i18n._(u'Enter task')
            )
        ).on_answer(self.set_title)
        self.done = data.done

    @property
    def data(self):
        return DataChecklistItem.get(self.id)

    @property
    def index(self):
        return self.data.index

    @property
    def checklist_id(self):
        return self.data.checklist.id

    def get_title(self):
        return self.data.title

    def set_title(self, title):
        self.data.title = title

    def set_done(self):
        '''toggle done status'''
        self.data.done = self.done = not self.done
        item = self.data
        data = {'item': self.get_title(),
                'list': item.checklist.title,
                'card': item.checklist.card.title}
        notifications.add_history(item.checklist.card.column.board,
                                  item.checklist.card,
                                  security.get_user().data,
                                  u'card_listitem_done' if self.done else u'card_listitem_undone',
                                  data)


class Checklist(object):

    def __init__(self, id_, data=None):
        self.id = id_
        data = data if data is not None else self.data
        self.items = [component.Component(ChecklistItem(item.id, item)) for item in data.items]

        self.title = component.Component(
            title.EditableTitle(
                self.get_title,
                placeholder=i18n._(u'Enter title')
            )
        ).on_answer(self.set_title)

        self.new_item = component.Component(NewChecklistItem())
        self.new_item.on_answer(self.add_item_from_str)

    def add_item_from_str(self, text):
        if text is None or not text.strip():
            return
        data_item = self.data.add_item_from_str(text)
        item = ChecklistItem(data_item.id, data_item)
        self.add_item(item)

    def add_item(self, item):
        item = component.Component(item)
        self.items.append(item)
        self.new_item().focus = True

    def remove_item(self, item):
        self.items.pop(item.index)
        self.data.remove_item(item.data)

    def delete_item(self, item):
        self.delete_index(item.index)

    def insert_item(self, index, item):
        self.data.insert_item(index, item.data)
        item = component.Component(item)
        self.items.insert(index, item)

    def delete_index(self, index):
        item = self.items.pop(index)
        self.data.delete_item(item().data)

    def get_title(self):
        return self.data.title

    def set_title(self, title):
        self.data.title = title

    def set_index(self, index):
        self.data.index = index
        return self

    @property
    def total_items(self):
        return len(self.items)

    @property
    def nb_items(self):
        return len([item for item in self.items if item().done])

    @property
    def progress(self):
        if not self.items:
            return 0
        return self.nb_items * 100 / self.total_items

    @property
    def data(self):
        return DataChecklist.get(self.id)

    def new_title(self, title):
        cl = self.data
        data = {'list': title, 'card': cl.card.title}
        notifications.add_history(cl.card.column.board,
                                  cl.card,
                                  security.get_user().data,
                                  u'card_add_list',
                                  data)


class Checklists(CardExtension):

    LOAD_PRIORITY = 30

    def __init__(self, card):
        super(Checklists, self).__init__(card)
        cklists = [(clist.id, Checklist(clist.id, clist)) for clist in card.get_datalists()]
        self.ck_cache = dict(cklists)
        self.checklists = [component.Component(clist) for __, clist in cklists]
        self.comp_id = str(random.randint(10000, 100000))

    @property
    def nb_items(self):
        return sum([cl().nb_items for cl in self.checklists])

    @property
    def total_items(self):
        return sum([cl().total_items for cl in self.checklists])

    def delete_checklist(self, index):
        cl = self.checklists.pop(index)()
        del self.ck_cache[cl.id]
        for i in range(index, len(self.checklists)):
            self.checklists[i]().set_index(i)
        data = {'list': cl.get_title(), 'card': self.card.get_title()}
        cl.data.delete()
        if data['list']:
            notifications.add_history(self.card.column.board.data,
                                      self.card.data,
                                      security.get_user().data,
                                      u'card_delete_list',
                                      data)

    def add_checklist(self):
        clist = DataChecklist(card=self.card.data)
        database.session.flush()
        ck = Checklist(clist.id, clist)
        self.ck_cache[clist.id] = ck
        ck.set_index(len(self.checklists))
        self.checklists.append(component.Component(ck))
        return ck

    def reorder(self, request, _resp):
        """Reorder checklists
        In:
         - ``ids`` -- checklist ids
        """
        ids = request.GET['data']
        cl_ids = map(lambda x: int(x.split('_')[-1]), json.loads(ids))
        self.checklists = [component.Component(self.ck_cache[cid].set_index(i))
                           for i, cid in enumerate(cl_ids)]

    def reorder_items(self, request, _resp):
        data = json.loads(request.GET['data'])
        item_id = int(data['id'].split('_')[-1])
        checklist_id = int(data['target'].split('_')[-1])
        item = ChecklistItem(item_id)
        source = self.ck_cache[item.checklist_id]
        checklist = self.ck_cache[checklist_id]
        source.remove_item(item)
        checklist.insert_item(data['index'], item)
