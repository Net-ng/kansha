# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import ajax, component, editor, presentation, validator as nagare_validator
from nagare.i18n import _

from kansha import validator
from kansha.toolbox import remote


class SaveTemplateEditor(object):
    def __init__(self, board):
        self.board = board
        self.title = editor.Property(board.get_title())
        self.title.validate(lambda v: nagare_validator.StringValidator(v).not_empty())
        self.description = editor.Property(board.description().text)
        self.shared = editor.Property(False).validate(validator.BoolValidator)

    def is_validated(self):
        return all(getattr(self, name).error is None for name in ('title', 'shared'))

    def cancel(self, comp):
        comp.answer(False)

    def commit(self, comp):
        if self.is_validated():
            comp.answer(True)

    def save(self):
        self.board.save_as_template(self.title.value, self.description.value, self.shared.value)


def close_overlay(comp):
    comp.answer(False)
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
            h << h.button(_('Cancel'), class_='btn').action(remote.Action(lambda: close_overlay(comp)))
    return h.root


@presentation.render_for(SaveTemplateEditor, 'loading')
def render_SaveTemplateEditor_loading(self, h, comp, *args):
    with h.div(class_='loading'):
        h << h.img(src='img/ajax-loader.gif')
        h << _(u'Please wait while board is saved...')

    update = ajax.Update(action=lambda *args: self.save(), render='saved')
    h << h.script(h.input(type='radio').action(update).get('onclick'))

    return h.root

@presentation.render_for(SaveTemplateEditor, 'saved')
def render_SaveTemplateEditor_saved(self, h, comp, *args):
    close = remote.Action(lambda: close_overlay(comp))
    close = h.input(type='radio').action(close).get('onclick')
    h << h.script('''YAHOO.kansha.app.onHideOverlay(function() { %s; });''' % close)
    with h.div(class_='success'):
        h << h.i(class_='icon-checkmark')
        h << _(u'Template saved!')
        with h.div(class_='buttons'):
            h << h.a(_(u'OK'), class_='btn btn-primary', onclick='''YAHOO.kansha.app.hideOverlay()''')
    return h.root


class SaveTemplateTask(component.Task):
    def __init__(self, board):
        self.board = board

    def go(self, comp):
        editor = component.Component(SaveTemplateEditor(self.board))
        ret = comp.call(editor)
        if ret:
            comp.call(editor, 'loading')
        comp.answer()