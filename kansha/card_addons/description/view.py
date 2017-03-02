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
    kw = {'class': 'description', 'id': id_}
    if security.has_permissions('edit', self.card):
        kw['onclick'] = h.a.action(comp.becomes, model='edit').get('onclick')
    with h.div(**kw):
        if self.text:
            h << h.parse_htmlstring(self.text, fragment=True)
        elif security.has_permissions('edit', self.card):
            h << h.textarea(placeholder=_("Add description."))

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
                h << h.a('bold', data_wysihtml_command='bold')
                h << h.a('italic', data_wysihtml_command='italic')
                h << h.a('underline', data_wysihtml_command='underline')
                h << h.a('ol', data_wysihtml_command='insertOrderedList')
                h << h.a('ul', data_wysihtml_command='insertUnorderedList')
                h << h.a('anchor', data_wysihtml_command='createLink')
                with h.div(data_wysihtml_dialog='createLink', style='display: none'):
                    with h.label:
                        h << h.input(data_wysihtml_dialog_field='href', value='http://',
                                     type='text', class_='text')
                    h << h.a('ok', data_wysihtml_dialog_action='save')
                    h << h.a('cancel', data_wysihtml_dialog_action='cancel')
            h << h.textarea(text(), id_=txt_id, class_='description-editor').action(text)
# <div id="wysihtml-toolbar" style="display: none;">
#   <a data-wysihtml-command="bold">bold</a>
#   <a data-wysihtml-command="italic">italic</a>

#   <!-- Some wysihtml5 commands require extra parameters -->
#   <a data-wysihtml-command="foreColor" data-wysihtml-command-value="red">red</a>
#   <a data-wysihtml-command="foreColor" data-wysihtml-command-value="green">green</a>
#   <a data-wysihtml-command="foreColor" data-wysihtml-command-value="blue">blue</a>

#   <!-- Some wysihtml5 commands like 'createLink' require extra paramaters specified by the user (eg. href) -->
#   <a data-wysihtml-command="createLink">insert link</a>
#   <div data-wysihtml-dialog="createLink" style="display: none;">
#     <label>
#       Link:
#       <input data-wysihtml-dialog-field="href" value="http://" class="text">
#     </label>
#     <a data-wysihtml-dialog-action="save">OK</a> <a data-wysihtml-dialog-action="cancel">Cancel</a>
#   </div>
# </div>

            with h.div(class_='buttons'):
                h << h.button(_('Save'), class_='btn btn-primary').action(lambda: change_text(self, comp, text()))
                h << ' '
                h << h.button(_('Cancel'), class_='btn').action(change_text, self, comp, None)
    h << h.script("""
        var editor = new wysihtml.Editor(%s, { // id of textarea element
          toolbar:      %s, // id of toolbar element
          parserRules:  wysihtmlParserRules, // defined in parser rules set
          style: true  // adopt styles of main page
        });
        document.getElementById("description").style.visibility = "visible";
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
