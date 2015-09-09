# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

from nagare import presentation, component, ajax, var
from nagare.i18n import _

from ..authentication.database import validators
from ..toolbox import overlay, remote
from .comp import User, PendingUser
from .usermanager import AddMembers, NewMember


@presentation.render_for(User)
def render_User(self, h, comp, *args):
    """Default view, render avatar and fullname"""
    h << comp.render(h, "avatar")
    with h.div(class_="name"):
        h << comp.render(h, model="fullname")
        h << h.span(self.data.email, class_="email")
    return h.root


@presentation.render_for(User, model='avatar')
def render_User_avatar(self, h, comp, model, *args):
    """Render a user's avatar"""
    with h.span(class_='avatar', title='%s' % (self.data.fullname)):
        h << h.img(src=self.get_avatar())
    return h.root


@presentation.render_for(User, model='fullname')
def render_User_fullname(self, h, comp, model, *args):
    """Render a user's avatar"""
    return h.span(self.data.fullname, class_="fullname")


@presentation.render_for(User, model='search')
def render_User_search(self, h, comp, *args):
    """Serach result view"""
    return h.div(comp)


@presentation.render_for(User, model='overlay-member')
@presentation.render_for(User, model='overlay-manager')
@presentation.render_for(User, model='overlay-remove')
@presentation.render_for(User, model='overlay-last_manager')
@presentation.render_for(PendingUser, model='overlay-pending')
def render_User_overlay_remove(self, h, comp, model):
    sub_model = model[8:]
    h << component.Component(
        overlay.Overlay(
            lambda r: (
                comp.render(r, "avatar"),
                {'class': 'miniavatar'}
            ),
            lambda r: comp.render(r, sub_model),
            dynamic=False,
            cls='card-overlay' if model == 'remove' else 'board-labels-overlay'
        )
    )
    return h.root


@presentation.render_for(User, "remove")
def render_User_remove(self, h, comp, *args):
    """Render for search result"""
    with h.div(class_='member'):
        h << comp.render(h, None)
        with h.span(class_="actions"):
            with h.form:
                h << h.input(value=_("Remove"), type="submit",
                             class_="btn btn-primary btn-small remove").action(ajax.Update(action=lambda: comp.answer(self.username)))
    return h.root


@presentation.render_for(User, "member")
@presentation.render_for(User, "manager")
def render_User_manager(self, h, comp, model):
    """Render for search result"""
    with h.div(class_='member'):
        h << comp.render(h, None)
        with h.span(class_="actions"):
            with h.form:
                h << h.input(
                        value=_("Manager"),
                        type="submit",
                        class_=("btn btn-primary btn-small toggle" if model == 'manager'
                                else "btn btn-primary btn-small")
                     ).action(ajax.Update(action=lambda: comp.answer('toggle_role')))
                h << h.input(
                        value=_("Remove"),
                        type="submit",
                        class_="btn btn-primary btn-small remove"
                    ).action(ajax.Update(action=lambda: comp.answer('remove')))
    return h.root


@presentation.render_for(User, "last_manager")
def render_User_last_manager(self, h, comp, *args):
    """Render for search result"""
    with h.div(class_='member'):
        h << comp.render(h, None)
        with h.span(class_="actions last-manager"):
            h << _("You are the last manager, you can't leave this board.")
    return h.root


@presentation.render_for(User, model="menu")
def render_User_menu(self, h, comp, *args):
    """Render user menu"""
    h << h.a(_("Home"), id="linkHome").action(lambda: comp.answer(self))
    h << h.a(_("Logout"), id="logout").action(comp.answer)
    return h.root


@presentation.render_for(User, model="detailed")
def render_User_detailed(self, h, comp, *args):
    """Render user detailed view"""
    h << h.h3(self.data.fullname)
    h << h.div(comp.render(h, model='avatar'))
    return h.root


@presentation.render_for(User, model="friend")
def render_User_friend(self, h, comp, *args):
    h << h.a(comp.render(h, "avatar")).action(
        remote.Action(lambda: comp.answer(self.data.email)))
    return h.root


@presentation.render_for(AddMembers)
def render_AddMembers(self, h, comp, *args):
    value = var.Var('')
    submit_id = h.generate_id('form')
    hidden_id = h.generate_id('hidden')

    with h.form:
        h << h.input(type='text', id=self.text_id)
        h << h.input(type='hidden', id=hidden_id).action(value)
        h << self.autocomplete
        h << h.script(u'''%(ac_id)s.itemSelectEvent.subscribe(function(sType, aArgs) {
    var value = aArgs[2][0];
    YAHOO.util.Dom.setAttribute('%(hidden_id)s', 'value', value);
    YAHOO.util.Dom.get('%(submit_id)s').click();
});''' % {'ac_id': self.autocomplete().var, 'hidden_id': hidden_id, 'submit_id': submit_id})
        h << h.script('''document.getElementById('%s').focus()''' % self.text_id, type='text/javascript', language='javascript')
        h << h.button(id=submit_id, style='display:none').action(remote.Action(lambda: comp.answer([] if not value() else [value()])))
    return h.root


@presentation.render_for(NewMember)
def render_NewMember(self, h, comp, *args):
    """Render the title of the associated card"""
    with h.form:
        members_to_add = var.Var()

        def get_emails():
            emails = []
            for email in members_to_add().split(','):
                try:
                    email = email.strip()
                    email = validators.validate_email(email)
                    emails.append(email)
                except ValueError:
                    continue
            return emails

        h << h.input(type='text', id=self.text_id,).action(members_to_add)
        h << h.input(value=_("Add"), type="submit",
                     class_="btn btn-primary btn-small"
                     ).action(remote.Action(lambda: comp.answer(get_emails())))
        h << self.autocomplete
    h << h.script("""document.getElementById('%s').focus()""" % self.text_id,
                  type="text/javascript", language="javascript")
    return h.root

# Pending User


@presentation.render_for(PendingUser)
def render_PendingUser(self, h, comp, *args):
    """Default view, render avatar and fullname"""
    h << comp.render(h, "avatar")
    with h.div(class_="name"):
        h << h.span(self.username, class_="fullname")
        h << h.span(self.username, class_="email")
    return h.root


@presentation.render_for(PendingUser, model='avatar')
def render_PendingUser_avatar(self, h, comp, model, *args):
    """Render a user's avatar"""
    with h.span(class_='avatar', title='%s' % (self.username)):
        h << h.img(src='img/pendingmember.png', class_="pending")
    return h.root


@presentation.render_for(PendingUser, "pending")
def render_PendingUser_pending(self, h, comp, *args):
    """Render for search result"""
    with h.div(class_='member'):
        h << comp.render(h, None)
        with h.span(class_="actions"):
            with h.form:
                h << h.input(value=_("Resend invitation"), type="submit",
                             class_="btn btn-primary btn-small").action(ajax.Update(action=lambda: comp.answer('resend')))
                h << h.input(value=_("Remove"), type="submit",
                             class_="btn btn-primary btn-small remove").action(ajax.Update(action=(lambda: comp.answer('remove'))))
    return h.root
