# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import component, editor, presentation, validator as nagare_validator
from nagare.i18n import _

from kansha import validator
from kansha.toolbox import remote


class SaveTemplateEditor(editor.Editor):
    def __init__(self, board):
        self.title = editor.Property(board.title().text)
        self.title.validate(lambda v: nagare_validator.StringValidator(v).not_empty())
        self.description = editor.Property(board.description().text)
        self.shared = editor.Property(False).validate(validator.BoolValidator)

    def cancel(self, comp):
        comp.answer(None)

    def commit(self, comp):
        if self.is_validated(('title', 'shared')):
            comp.answer((self.title.value, self.description.value, self.shared.value))

    def close(self, comp):
        comp.answer()
        return 'YAHOO.kansha.app.hideOverlay()'


@presentation.render_for(SaveTemplateEditor)
def render_SaveTemplateEditor(self, h, comp, *args):
    with h.form(class_='description-form'):
        with h.div:
            id_ = h.generate_id()
            h << h.label(_(u'Title'), for_=id_)
            h << h.input(type='text', value=self.title()).error(self.title.error).action(self.title)
        with h.div:
            id_ = h.generate_id()
            h << h.label(_(u'Description'), for_=id_)
            h << h.textarea(self.description()).action(self.description)

        with h.div:
            id_ = h.generate_id()
            h << h.label(_(u'Save for'), for_=id_)
            with h.select(id_=id_).error(self.shared.error).action(self.shared):
                h << h.option(_(u'Me only'), value='').selected(not self.shared())
                h << h.option(_(u'All users'), value='on').selected(self.shared())

        with h.div(class_='buttons'):
            h << h.button(_(u'Save'), class_='btn btn-primary', type='submit').action(self.commit, comp)
            h << ' '
            h << h.button(_('Cancel'), class_='btn').action(remote.Action(lambda: self.close(comp)))
    return h.root


@presentation.render_for(SaveTemplateEditor, 'saved')
def render_SaveTemplateEditor_saved(self, h, comp, *args):
    close = remote.Action(lambda: self.close(comp))
    close = h.input(type='radio').action(close).get('onclick')
    h << h.script('''YAHOO.kansha.app.onHideOverlay(function() { %s; });''' % close)
    h << h.div(h.i(class_='icon-checkmark'), _(u'Template saved!'), class_='success')
    with h.div(class_='buttons'):
        h << h.a(_(u'OK'), class_='btn btn-primary', onclick='''YAHOO.kansha.app.hideOverlay()''')
    return h.root


class SaveTemplateTask(component.Task):
    def __init__(self, board):
        self.board = board

    def go(self, comp):
        editor = component.Component(SaveTemplateEditor(self.board))
        ret = comp.call(editor)
        if ret is not None:
            title, description, shared = ret
            self.board.save_as_template(title, description, shared)
            comp.call(editor, 'saved')
        comp.answer()