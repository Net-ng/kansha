# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare.i18n import _
from nagare import presentation, var, security, ajax

from .comp import CardDescription


@presentation.render_for(CardDescription)
def render(self, h, comp, *args):
    """Render description component.

    If text is empty, display a text area otherwise it's a simple text
    """
    id_ = h.generate_id()
    kw = {'class': 'description-content', 'id': id_}
    if security.has_permissions('edit', self.card):
        kw['onclick'] = h.a.action(comp.becomes, model='edit').get('onclick')
    with h.div(**kw):
        if self.text:
            h << h.parse_htmlstring(self.text, fragment=True)
        elif security.has_permissions('edit', self.card):
            h << h.textarea(placeholder=_("Add a description. URL in the text are automatically recognized as links."))

    h << h.script("YAHOO.kansha.app.urlify($('#' + %s))" % ajax.py2js(id_))
    h << h.script('if (typeof editor != "undefined") { editor.destroy(); editor = undefined; }')
    return h.root


def change_text(description, comp, text):
    description.change_text(text)
    comp.becomes(model=None)


@presentation.render_for(CardDescription, model='edit')
def render_edit(self, h, comp, *args):
    """Render description component in edit mode"""
    text = var.Var(self.text)
    with h.div(id_="description", style='visibility: hidden'):
        with h.form(class_='description-form'):
            txt_id = h.generate_id()
            with h.div(id_=txt_id + '-toolbar'):
                h << h.a(h.i(class_='icon-bold'), data_wysihtml_command='bold',
                         class_='btn icon-btn', title=_('bold')) << ' '
                h << h.a(h.i(class_='icon-italic'), data_wysihtml_command='italic',
                         class_='btn icon-btn', title=_('italic')) << ' '
                h << h.a(h.i(class_='icon-underline'), data_wysihtml_command='underline',
                         class_='btn icon-btn', title=_('underline')) << ' '
                h << h.a(h.i(class_='icon-list-numbered'), data_wysihtml_command='insertOrderedList',
                         class_='btn icon-btn', title=_('numbered list')) << ' '
                h << h.a(h.i(class_='icon-list2'), data_wysihtml_command='insertUnorderedList',
                         class_='btn icon-btn', title=_('bullet list')) << ' '
                h << h.a(h.i(class_='icon-link'), data_wysihtml_command='createLink',
                         class_='btn icon-btn', title=_('link')) << ' '
                with h.div(data_wysihtml_dialog='createLink', class_='editor-popin',
                           style='display:none'):
                    with h.label:
                        h << h.input(data_wysihtml_dialog_field='href', value='http://',
                                     type='text', class_='text')
                    h << h.a(_('Link'), data_wysihtml_dialog_action='save', class_='btn btn-primary')
                    h << h.a(_('Cancel'), data_wysihtml_dialog_action='cancel', class_='btn')
            h << h.textarea(
                text(), id_=txt_id,
                class_='description-editor description-content').action(text)

            with h.div(class_='buttons'):
                h << h.button(_('Save'), class_='btn btn-primary').action(lambda: change_text(self, comp, text()))
                h << ' '
                h << h.button(_('Cancel'), class_='btn').action(change_text, self, comp, None)
    h << h.script("""
        var editor = new wysihtml.Editor(%s, { // id of textarea element
          toolbar:      %s, // id of toolbar element
          parserRules:  wysihtmlParserRules, // defined in parser rules set
          style: true,  // adopt styles of main page
          // FIXME: no hard coded path to theme; extensions should have a mechanism to load their styles
          stylesheets: ['/static/kansha/css/themes/kansha_flat/board.css'] // adoption is not complete
        });
        document.getElementById("description").style.visibility = "visible";
        editor.focus();
        """ % (ajax.py2js(txt_id), ajax.py2js(txt_id + '-toolbar'))
    )
    return h.root


@presentation.render_for(CardDescription, model='badge')
def render_badge(self, h, *args):
    """Render description component as a card badge"""
    if self.text:
        with h.span(class_='badge'):
            h << h.span(h.i(class_='icon-pencil'), class_='label')
    return h.root
