Frequently Asked Questions
==========================

How can I change the design of a Kansha app?
--------------------------------------------

Kansha supports custom themes, a default theme called *kansha_flat* is bundled with the app.

A theme is made of 4 CSS files grouped in a folder named as your theme:

  - ``kansha.css`` is included in every page, it should contain common style rules used all around the app

  - ``board.css`` is included in the board view, it defines the styles of the boards, colums and cards

  - ``home.css`` is only included in the homepage listing your boards and in user profile/user cards

  - ``login.css`` is included in the login page only

For development purposes you can store it in the folder */static/css/themes/* or configure a web server to serve these files according to `deployment section of the Nagare manual <http://www.nagare.org/trac/wiki/ApplicationDeployment#configuring-the-web-server>`_.

To activate it, you have to edit the :ref:`application` section of your configuration file, changing the ``theme`` parameter to fit your theme name.

Once done, restart your app and enjoy.

See :file:`static/css/themes/kansha_flat` folder for a working example.

