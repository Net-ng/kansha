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

from peak.rules import when

from nagare.i18n import _
from nagare.security import common
from nagare import component, database, i18n, security

from kansha import title
from kansha.card import Card
from kansha.services.search import schema
from kansha.cardextension import CardExtension
from kansha.services.actionlog.messages import render_event

from .models import DataChecklist, DataChecklistItem


@when(common.Rules.has_permission, "user and perm == 'checklist' and isinstance(subject, Card)")
def has_permission_Card_checklist(self, user, perm, card):
    return security.has_permissions('edit', card)


@when(render_event, "action=='card_add_list'")
def render_event_card_add_list(action, data):
    return _(u'User %(author)s has added the checklist "%(list)s" to card "%(card)s"') % data


@when(render_event, "action=='card_delete_list'")
def render_event(action, data):
    return _(u'User %(author)s has deleted the checklist "%(list)s" from card "%(card)s"') % data


@when(render_event, "action=='card_listitem_done'")
def render_event(action, data):
    return _(u'User %(author)s has checked the item %(item)s from the checklist "%(list)s", on card "%(card)s"') % data


@when(render_event, "action=='card_listitem_undone'")
def render_event(action, data):
    return _(u'User %(author)s has unchecked the item %(item)s from the checklist "%(list)s", on card "%(card)s"') % data


class NewChecklistItem(object):
    def __init__(self, show_button):
        self.show_button = show_button
        self.focus = False

    def set_show_button(self, show_button):
        self.show_button = show_button
        if not show_button:
            self.focus = True


class ChecklistItem(object):

    def __init__(self, id_, action_log, data=None):
        self.id = id_
        self.action_log = action_log
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
        self.action_log.add_history(
            security.get_user(),
            u'card_listitem_done' if self.done else u'card_listitem_undone',
            data)


class Checklist(object):
    def __init__(self, id_, action_log, data=None):
        self.id = id_
        self.action_log = action_log
        data = data if data is not None else self.data
        self.items = [component.Component(ChecklistItem(item.id, action_log, item)) for item in data.items]

        self.title = component.Component(
            title.EditableTitle(
                self.get_title,
                placeholder=i18n._(u'Add title')
            )
        ).on_answer(self.set_title)
        self.new_item = component.Component(NewChecklistItem(len(self.items))).on_answer(self.add_item_from_str)

    def update(self, other):
        self.data.update(other.data)
        self.items = [component.Component(ChecklistItem(item.id, self.action_log, item)) for item in self.data.items]

    def add_item_from_str(self, text):
        if text is None or not text.strip():
            return
        data_item = self.data.add_item_from_str(text)
        item = ChecklistItem(data_item.id, self.action_log, data_item)
        self.add_item(item)

    def add_item(self, item):
        item = component.Component(item)
        self.items.append(item)
        # UI specific
        if self.new_item:
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
        if not self.data.title:
            self.new_title(title)
        self.data.title = title

    def set_index(self, index):
        self.data.index = index
        return self

    def delete(self):
        self.items = []
        self.data.purge()
        self.data.delete()

    @property
    def total_items(self):
        return len(self.items)

    @property
    def total_items_done(self):
        return len([item for item in self.items if item().done])

    @property
    def progress(self):
        if not self.items:
            return 0
        return self.total_items_done * 100 / self.total_items

    @property
    def data(self):
        return DataChecklist.get(self.id)

    def new_title(self, title):
        cl = self.data
        data = {'list': title, 'card': cl.card.title}
        self.action_log.add_history(
                                  security.get_user(),
                                  u'card_add_list',
                                  data)


class Checklists(CardExtension):

    LOAD_PRIORITY = 30

    def __init__(self, card, action_log, configurator):
        super(Checklists, self).__init__(card, action_log, configurator)
        self.ck_cache = {}
        self.checklists = []

    def load_children(self):
        if not self.checklists:
            cklists = [(clist.id, Checklist(clist.id, self.action_log, clist)) for clist in self.data]
            self.ck_cache = dict(cklists)
            self.checklists = [component.Component(clist) for __, clist in cklists]

    @staticmethod
    def get_schema_def():
        return schema.Text(u'checklists')

    def update_document(self, document):
        document.checklists = u'\n'.join(cl.to_indexable() for cl in self.data)

    @property
    def data(self):
        return DataChecklist.get_by_card(self.card.data)

    def update(self, other):
        other.load_children()
        for index, checklist in enumerate(other.checklists):
            checklist = checklist()
            new_checklist = self.add_checklist()
            new_checklist.update(checklist)

    @property
    def total_items(self):
        return DataChecklist.total_items(self.card.data)

    @property
    def total_items_done(self):
        return DataChecklist.total_items_done(self.card.data)

    def delete_checklist(self, index):
        cl = self.checklists.pop(index)()
        del self.ck_cache[cl.id]
        for i in range(index, len(self.checklists)):
            self.checklists[i]().set_index(i)
        data = {'list': cl.get_title(), 'card': self.card.get_title()}
        cl.delete()
        if data['list']:
            self.action_log.add_history(
                                      security.get_user(),
                                      u'card_delete_list',
                                      data)

    def delete(self):
        self.load_children()
        for checklist in self.ck_cache.values():
            checklist.delete()

    def add_checklist(self):
        clist = DataChecklist(card=self.card.data)
        database.session.flush()
        ck = Checklist(clist.id, self.action_log, clist)
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
        item = ChecklistItem(item_id, self.action_log)
        source = self.ck_cache[item.checklist_id]
        checklist = self.ck_cache[checklist_id]
        source.remove_item(item)
        checklist.insert_item(data['index'], item)
