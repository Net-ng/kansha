First connection
================

Kansha works with Firefox, Chrome, Internet Explorer 9 and above, Safari 7 and above.

Login screen
------------

.. figure:: _static/login_screen.png

   Login screen with all authentication methods enabled

Kansha supports three different authentication schemes:

* :ref:`dbauth`
* :ref:`ldapauth`
* :ref:`oauth` (Google, Facebook, Twitter…)

The administrator of Kansha may choose to enable one or several of those authentication methods. So, your actual login screen may differ from the one pictured above.

The installer created several demonstration accounts for you. They are: user1, user2, user3. They all have the same password: *password*.

.. _dbauth:

Database authentication
^^^^^^^^^^^^^^^^^^^^^^^

To be able to login with that form, you need to register an account first, by clicking on the *create one* link.

When you submit the registration form, an email is sent to you to verify your email address, or to a moderator who will verify your identity.
The actual registration process depends on the site policy.

If Kansha sends you an email, just follow the instructions. Basically, you have to click on a link to confirm your email address. Then your can login with your credentials.

If the registration is moderated, you may be contacted by the moderator. Eventually, the moderator will inform you when your account is activated or denied.

.. _ldapauth:

LDAP authentication
^^^^^^^^^^^^^^^^^^^

If LDAP authentication is enabled, you can login to Kansha with the credentials you already use to sign on the other applications of your company.

.. _oauth:

OAuth authentication
^^^^^^^^^^^^^^^^^^^^

OAuth authentication allows users of third party applications to log in Kansha.

The administrator of Kansha may grant access to users of:

* Google,
* Twitter,
* Facebook,
* Github.

..
    * Dropbox,
    * Salesforce,
    * Flickr,
    * Vimeo,
    * Bitbucket,
    * Yahoo,
    * Dailymotion,
    * Viadeo,
    * Linkedin,
    * Foursquare,
    * or Instagram.


Home
----

When you first login, you arrive straight on your *Home page*.

.. figure:: _static/home.png

   The home page of a very active user.

On the home screen you have access to:

* the list of the boards you can participate in (see :ref:`board_access`);
* your profile, which you can edit.

On the board tab, the boards you have access to are organized as follows:

 - The 5 last modified boards, for direct access to hot boards;
 - your boards, i.e. the boards you are manager of;
 - guest boards, i.e. the boards you are just member of;
 - shared boards, i.e. all the boards that are public and shared on this Kansha instance.

If you are logging on a freshly installed Kansha instance, the board list is empty.

On your profile, you can change the language of the interface. If your favorite language is missing, consider :ref:`contributing <contribute_trans>`.

You are encouraged to upload a picture of your face on your profile.


Your first board
----------------

Let's create your first board!

In the template drop-down menu, chose "Todo" then click on the "Create" button.

.. figure:: _static/create_board.png

   Create your first board.

Your newly created board automatically opens.

.. figure:: _static/your_first_board.png

   This is how your first todo board looks like

Now adds a few card by using the menus at the bottom of the lists. Columns are called lists in Kansha.

Now try these:

* add new lists by using the board menu;
* change the board title by clicking on it;
* drag some cards around;
* open a card by clicking on it and discover its features;
* explore the board menu;
* make your own experiments.


Anatomy of a board
------------------

.. figure:: _static/welcome_board.png

   A board with some cards and list limits.

In Kansha, a board is made of columns, also known as lists, that contain cards. You can add as many columns as you wish to a board.

Columns can be reordered by dragging and dropping them. Cards can be moved accross columns and reordered the same way.

To open a card, just click on it.

Take some time to play with the cards on your board. For now your board is private and you can safely experiment without causing trouble to other users.

On a card you can:

* edit the title;
* add/remove *labels* (tags);
* edit a description;
* comment;
* add and check check-lists;
* add files;
* vote (if activated by the board owner, see :ref:`board_configuration`);
* give it some weight (if activated by the board owner, see :ref:`board_configuration`);
* set a due date;
* assign members to it (if you have invited other users to your board, see :ref:`board_access`).

The columns may have a limit on the number of cards they accept. This limit is displayed after the slash in the column counter. To activate the counter, click on the list menu. To set the limit, just click on the counter.

To change titles just click on them. That works for:

* cards;
* columns;
* board.

Now, look at the switches in the upper right corner of the screen. By default, *board mode* is activated. If you click on *calendar mode*, the screen displays a view of the current month where you can see the cards that expire that month.

Last, consider the main tabs. The **Kansha** one gives you access to your *home* (next section). The **Board** one contains everything you need to manage the current board.

Board operations available in the **Board** tab (for members only):

Preferences
    This menu allows you to configure the board and to subscribe to notifications. Board configuration is covered in :ref:`board_configuration`. Notifications will be sent to you by email.
Add list
    Add a new column.
Edit board description
    Describe here what the board is for.
Export board
    Export all cards as lines in an XLS file.
Save as template (requires management role)
    Save the current board as a template.
Action Log
    The *Action log* displays the history of the actions that happened on the current board. Open it and see what you have done in this board so far.
Delete board / Leave this board
    Respectively on boards you own and boards you are simply a member of, those actions just do what you would expect.



Searching
---------

Use the search input to search the cards.

Type your query terms here: the irrelevant cards are filtered out as you type and the matching cards are highlighted.

The search engine looks at the title, description, comments and labels of cards.