# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import datetime

from nagare import component, security
from nagare.database import session

from .models import DataComment
from ..user import usermanager
from ..flow import comp as flow
from .. import notifications, validator


class Comment(flow.FlowElement):

    """Comment component"""

    def __init__(self, data):
        """Initialization

        In:
            - ``data`` -- the comment object from the database
        """
        self.db_id = data.id
        self.text = data.comment
        self.creation_date = data.creation_date
        self.author = component.Component(usermanager.get_app_user(data.author.username, data=data.author))
        self.comment_label = component.Component(Commentlabel(self))
        self.comment_label.on_answer(lambda v: self.comment_label.call(model='edit'))

    def edit_comment(self):
        self.comment_label.call(model='edit')

    def is_author(self, user):
        return self.author().username == user.username

    def set_comment(self, text):
        if text is None:
            return
        text = text.strip()

        if text:
            self.data.comment = validator.clean_text(text)

    @property
    def data(self):
        """Return the comment object from the database
        """
        return DataComment.get(self.db_id)


class Commentlabel(object):

    """comment label component.

    """

    def __init__(self, parent):
        """Initialization

        In:
          - ``parent`` -- parent of comment label
        """
        self.parent = parent
        self.text = parent.text or u''

    def change_text(self, text):
        """Change the comment of our wrapped object

        In:
            - ``text`` -- the new comment
        Return:
            - the new comment

        """
        if text is None:
            return
        text = text.strip()
        if text:
            text = validator.clean_text(text)
            self.text = text
            self.parent.set_comment(text)
            return text

    def is_author(self, user):
        return self.parent.is_author(user)


class Comments(flow.FlowSource):

    """Comments component
    """

    def __init__(self, parent, data_comments=()):
        """Initialization

        In:
            - ``parent`` -- the parent card
            - ``comments`` -- the comments of the card
        """
        self.parent = parent
        self.comments = [self._create_comment_component(data_comment) for data_comment in data_comments]

    @property
    def flow_elements(self):
        return self.comments

    def _create_comment_component(self, data_comment):
        return component.Component(Comment(data_comment)).on_answer(self.delete)

    def add(self, v):
        """Add a new comment to the card

        In:
            - ``v`` -- the comment content
        """
        security.check_permissions('comment', self.parent)
        if v is None:
            return
        v = v.strip()
        if v:
            v = validator.clean_text(v)
            user = security.get_user()
            comment = DataComment(comment=v.strip(), card_id=self.parent.data.id,
                                  author=user.data, creation_date=datetime.datetime.utcnow())
            session.add(comment)
            session.flush()
            data = {'comment': v.strip(), 'card': self.parent.title().text}
            notifications.add_history(self.parent.column.board.data, self.parent.data, security.get_user().data, u'card_add_comment', data)
            self.comments.insert(0, self._create_comment_component(comment))

    def delete(self, comp):
        """Delete a comment.

        In:
            - ``comment`` -- the comment to delete
        """
        self.comments.remove(comp)
        comment = comp()
        DataComment.get(comment.db_id).delete()
        session.flush()
