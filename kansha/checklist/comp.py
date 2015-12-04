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
from kansha.services.components_repository import CardExtension

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
        self.new_item.on_answer(self.add_item)

    def reorder_items(self):
        for i, item in enumerate(self.data.items):
            item.index = i

    def add_item(self, text):
        if text is None or not text.strip():
            return
        item = DataChecklistItem(checklist=self.data, title=text.strip(), index=len(self.data.items))
        database.session.flush()
        item = component.Component(ChecklistItem(item.id, item))
        self.items.append(item)
        self.reorder_items()
        self.new_item().focus = True

    def delete_item(self, index):
        item = self.items.pop(index)()
        item.data.delete()
        self.reorder_items()

    def get_title(self):
        return self.data.title

    def set_title(self, title):
        self.data.title = title

    def set_index(self, index):
        self.data.index = index

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
        self.parent = card
        self.checklists = [component.Component(Checklist(clist.id, clist)) for clist in card.get_datalists()]
        self.comp_id = str(random.randint(10000, 100000))

    def copy(self, parent, additional_data):
        new_extension = super(Checklists, self).copy(parent, additional_data)
        for index, checklist in enumerate(self.checklists):
            checklist = checklist()
            new_data_checklist = DataChecklist(card=parent.data,
                                               title=checklist.data.title)
            database.session.flush()
            new_checklist = Checklist(new_data_checklist.id, new_data_checklist)
            new_checklist.set_index(index)
            for item in checklist.items:
                item = item()
                new_checklist.add_item(item.data.title)
            new_extension.checklists.append(component.Component(new_checklist))
        return new_extension

    @property
    def nb_items(self):
        return sum([cl().nb_items for cl in self.checklists])

    @property
    def total_items(self):
        return sum([cl().total_items for cl in self.checklists])

    def delete_checklist(self, index):
        cl = self.checklists.pop(index)()
        for i in range(index, len(self.checklists)):
            self.checklists[i]().set_index(i)
        data = {'list': cl.get_title(), 'card': self.parent.get_title()}
        cl.data.delete()
        if data['list']:
            notifications.add_history(self.parent.column.board.data,
                                      self.parent.data,
                                      security.get_user().data,
                                      u'card_delete_list',
                                      data)

    def add_checklist(self):
        clist = DataChecklist(card=self.parent.data)
        database.session.flush()
        ck = Checklist(clist.id, clist)
        ck.set_index(len(self.checklists))
        self.checklists.append(component.Component(ck))

    def reorder(self, ids):
        """Reorder checklists
        In:
         - ``ids`` -- checklist ids
        """
        new_order = []
        i = 0
        for cl_id in json.loads(ids):
            id_ = int(cl_id.split('_')[-1])
            for cl in self.checklists:
                if cl().id == id_:
                    cl().set_index(i)
                    i += 1
                    new_order.append(cl)
        self.checklists = new_order

    def reorder_items(self, data):
        data = json.loads(data)
        item_id = int(data['id'].split('_')[-1])
        checklist_id = int(data['target'].split('_')[-1])
        item = DataChecklistItem.get(item_id)
        checklist = DataChecklist.get(checklist_id)
        source = item.checklist
        item.checklist = None
        checklist.items.insert(data['index'], item)
        source.reorder_items()
        checklist.reorder_items()
        self.parent.reload()
