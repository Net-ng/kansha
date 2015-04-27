#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation, security, var, ajax
from nagare.i18n import _

from comp import NewChecklistItem, ChecklistTitle, ChecklistItemTitle, Checklists, Checklist, ChecklistItem


@presentation.render_for(NewChecklistItem)
def render_ChecklistTitle_edit(next_method, self, h, comp, *args):
    """Render the title of the associated object"""
    text = var.Var(u'')
    with h.form(class_='new-item-form'):
        id_ = h.generate_id()
        h << h.input(type='text', value=text, id_=id_, placeholder=_(u'Add item')).action(text)
        with h.div(class_='btn-group'):
            h << h.button(h.i(class_='icon-grey icon-ok'),
                          class_='btn btn-small').action(lambda: comp.answer(text()))
            h << h.button(h.i(class_='icon-grey icon-remove'), class_='btn btn-small').action(comp.answer)

    if self.focus:
        h << h.script('''YAHOO.util.Dom.get("%(id)s").focus();''' % {'id': id_})
        self.focus = False
    return h.root


@presentation.render_for(ChecklistTitle)
def render_ChecklistTitle(self, h, comp, *args):
    """Render the title of the associated object"""
    h << h.i(class_='icon-th-list icon-grey')
    kw = {}
    kw['style'] = 'cursor: pointer;display: inline;'
    kw['onclick'] = h.a.action(comp.answer).get('onclick').replace('return', "")
    with h.div(class_='text-title', **kw):
        content = self.text or h.span(_('Edit title'), class_='show_onhover')
        h << content

    return h.root


@presentation.render_for(ChecklistTitle, model='edit')
def render_ChecklistTitle_edit(next_method, self, h, comp, *args):
    """Render the title of the associated object"""
    text = var.Var(self.text)
    with h.form(class_='title-form'):
        id_ = h.generate_id()
        h << h.i(class_='icon-th-list icon-grey')
        h << h.input(type='text', value=text, id_=id_, placeholder=_(u'Checklist title')).action(text)
        with h.div(class_='btn-group'):
            h << h.button(h.i(class_='icon-grey icon-ok'), class_='btn btn-small').action(lambda: comp.answer(self.change_text(text())))
            h << h.button(h.i(class_='icon-grey icon-remove'), class_='btn btn-small').action(comp.answer)
    h << h.script('''YAHOO.util.Dom.get("%(id)s").focus();''' % {'id': id_})
    return h.root


@presentation.render_for(ChecklistItemTitle)
def render_ChecklistTitle(self, h, comp, *args):
    """Render the title of the associated object"""
    return h.a(self.text).action(comp.answer)


@presentation.render_for(ChecklistItemTitle, model='edit')
def render_ChecklistTitle_edit(next_method, self, h, comp, *args):
    """Render the title of the associated object"""
    text = var.Var(self.text)
    with h.form(class_='item-title-form'):
        id_ = h.generate_id()
        h << h.input(type='text', value=text, id_=id_, placeholder=_(u'Checklist title')).action(text)
        with h.div(class_='btn-group'):
            h << h.button(h.i(class_='icon-grey icon-ok'), class_='btn btn-small').action(lambda: comp.answer(self.change_text(text())))
            h << h.button(h.i(class_='icon-grey icon-remove'), class_='btn btn-small').action(comp.answer)
    h << h.script('''YAHOO.util.Dom.get("%(id)s").focus();''' % {'id': id_})
    return h.root


@presentation.render_for(Checklists, 'button')
def render_Checklists_button(self, h, comp, model):
    if security.has_permissions('checklist', self.parent):
        with h.a(class_='btn btn-small btn-checklist').action(self.add_checklist):
            h << h.i(class_='icon-th-list icon-grey')
            h << _('Checklist')
    return h.root


@presentation.render_for(Checklists)
def render_Checklists(self, h, comp, model):
    if security.has_permissions('checklist', self.parent):

        # On drag and drop
        action = ajax.Update(action=self.reorder)
        action = '%s;_a;%s=' % (h.add_sessionid_in_url(sep=';'), action._generate_replace(1, h))
        h.head.javascript(h.generate_id(), '''function reorder_checklists(data) {
            nagare_getAndEval('%s' + YAHOO.lang.JSON.stringify(data));
        }''' % action)

        id_ = h.generate_id()
        with h.div(class_='checklists', id=id_):
            for index, clist in enumerate(self.checklists):
                h << clist.on_answer(lambda v, index=index: self.delete_checklist(index))
        h << h.script("""$(function() {
        $( "#%(id)s" ).sortable({
          placeholder: "ui-state-highlight",
          axis: "y",
          handle: ".icon-th-list.icon-grey",
          cursor: "move",
          stop: function( event, ui ) { reorder_checklists($('.checklist').map(function() { return this.id }).get()) }
        });
      });""" % {'id': id_})
    return h.root


@presentation.render_for(Checklists, 'badge')
def render_Checklists_badge(self, h, comp, model):
    if self.checklists:
        h << h.span(h.i(class_='icon-th-list icon-grey'), ' ', self.nb_items, u' / ', self.total_items, class_='label')
    return h.root


@presentation.render_for(Checklist)
def render_Checklist(self, h, comp, model):
    with h.div(id='checklist_%s' % self.id, class_='checklist'):
        with h.div(class_='title'):
            h << self.title
            if self.title.model != 'edit':
                h << h.a(h.i(class_='icon-remove icon-grey'), class_='delete').action(comp.answer, 'delete')

        with h.div(class_='content'):
            if self.items:
                h << comp.render(h, 'progress')
            with h.ul:
                for index, item in enumerate(self.items):
                    h << h.li(item.on_answer(lambda v, index=index: self.delete_item(index)))
            h << self.new_item
    return h.root


@presentation.render_for(Checklist, 'progress')
def render_Checklist_progress(self, h, comp, model):
    progress = self.progress
    with h.div(class_='progress progress-success'):
        h << h.div(class_='bar', style='width:%s%%' % progress)
        h << h.span(progress, u'%', class_='percent')
    return h.root


@presentation.render_for(ChecklistItem)
def render_ChecklistItem(self, h, comp, model):
    h << h.a(u'\u2611' if self.done else u'\u2610', class_='check').action(self.set_done)
    h << h.span(self.title, class_='done' if self.done else '')
    if not self.title.model == 'edit':
        h << h.a(h.i(class_='icon-remove icon-grey'), class_='delete').action(comp.answer, 'delete')
    return h.root
