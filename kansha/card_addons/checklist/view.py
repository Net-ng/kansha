#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.i18n import _
from nagare import presentation, security, var, ajax

from .comp import Checklist, ChecklistItem, Checklists, NewChecklistItem


@presentation.render_for(NewChecklistItem, 'button')
def render_NewChecklistItem_button(self, h, comp, model):
    return h.a(h.i(class_='icon-plus'), class_='add-item', title=_(u'Add item')).action(comp.answer)


@presentation.render_for(NewChecklistItem, 'edit')
def render_NewChecklistItem_edit(self, h, comp, model):
    """Render the title of the associated object"""
    text = var.Var(u'')
    with h.form(class_='new-item-form'):
        id_ = h.generate_id()
        h << h.div(
            h.input(type='text', value=text, id_=id_, placeholder=_(u'Add item')).action(text)
        )
        h << h.button(_(u'Add'),
                      class_='btn btn-primary').action(lambda: comp.answer(text()))

    if self.focus:
        h << h.script("YAHOO.util.Dom.get(%s).focus()" % ajax.py2js(id_))
        self.focus = False
    return h.root


@presentation.render_for(Checklists, 'action')
def render_Checklists_button(self, h, comp, model):
    if security.has_permissions('checklist', self.card):
        action = ajax.Update(render=lambda r: comp.render(r, model=None),
                             component_to_update='clists',
                             action=self.add_checklist)
        with h.a(class_='btn').action(action):
            h << h.i(class_='icon-list')
            h << _('Checklist')
    return h.root


@presentation.render_for(Checklists)
def render_Checklists(self, h, comp, model):
    h.head.javascript_url('checklists/js/checklists.js')
    self.load_children()
    can_edit = security.has_permissions('checklist', self.card)
    with h.div(id_='clists'):
        if can_edit:

            # On drag and drop
            action = h.a.action(ajax.Update(action=self.reorder, with_request=True)).get('onclick').replace('return', '')
            action = action.replace('")', '&data="+ YAHOO.lang.JSON.stringify(data))')
            h.head.javascript(h.generate_id(), '''function reorder_checklists(data) {
                %s;
            }''' % action)

            # On items drag and drop
            action = h.a.action(ajax.Update(action=self.reorder_items, with_request=True)).get('onclick').replace('return', '')
            action = action.replace('")', '&data="+ YAHOO.lang.JSON.stringify(data))')
            h.head.javascript(h.generate_id(), '''function reorder_checklists_items(data) {
                    %s;
                }''' % action)

        id_ = h.generate_id()
        with h.div(class_='checklists', id=id_):
            for index, clist in enumerate(self.checklists):
                if can_edit:
                    h << clist.on_answer(
                        lambda v, index=index: self.delete_checklist(index)
                    )
                else:
                    h << clist.render(h, 'read-only')
    return h.root


@presentation.render_for(Checklists, 'badge')
def render_Checklists_badge(self, h, comp, model):
    total_items = self.total_items
    if total_items:
        with h.span(class_='badge'):
            h << h.span(h.i(class_='icon-list'), ' ', self.total_items_done, ' / ', total_items, class_='label')
    return h.root


@presentation.render_for(Checklist)
@presentation.render_for(Checklist, 'read-only')
def render_Checklist(self, h, comp, model):
    with h.div(id='checklist_%s' % self.id, class_='checklist'):
        with h.div(class_='title'):
            h << h.i(class_='icon-list')
            if model == 'read-only':
                h << self.data.title
            else:
                h << self.title.render(h.AsyncRenderer())
                h << h.a(h.i(class_='icon-cross'), class_='delete').action(
                    ajax.Update(render='deleted', action=comp.answer)
                )

        with h.div(class_='content'):
            if self.items:
                h << comp.render(h, 'progress')
            with h.ul:
                for index, item in enumerate(self.items):
                    if model == 'read-only':
                        h << h.li(item.render(h, 'read-only'))
                    else:
                        h << h.li(item.on_answer(lambda v, index=index: self.delete_index(index)),
                                  id='checklist_item_%s' % item().id)
            if model != 'read-only':
                h << self.new_item
    return h.root


@presentation.render_for(Checklist, 'progress')
def render_Checklist_progress(self, h, comp, model):
    progress = self.progress
    with h.div(class_='progress progress-success'):
        h << h.div(class_='bar', style='width:%s%%' % progress)
        h << h.span(progress, u'%', class_='percent')
    return h.root


@presentation.render_for(Checklist, 'deleted')
def render_Checklist_progress(self, h, comp, model):
    h << h.div()
    return h.root


@presentation.render_for(ChecklistItem, model='read-only')
def render_ChecklistItem(self, h, comp, model):
    h << h.span(h.i(class_='icon-checkbox-' + ('checked' if self.done else 'unchecked')))
    h << h.span(self.data.title, class_='done' if self.done else '')
    return h.root


@presentation.render_for(ChecklistItem)
def render_ChecklistItem(self, h, comp, model):
    h << h.a(h.i(class_='icon-checkbox-' + ('checked' if self.done else 'unchecked'))).action(self.set_done)
    h << h.span(self.title.render(h.AsyncRenderer()), class_='done' if self.done else '')
    h << h.a(h.i(class_='icon-cross'), class_='delete').action(comp.answer, 'delete')
    return h.root
