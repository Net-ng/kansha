.. _configuration_guide:

Configuration Guide
===================

In the following, <VENV_DIR> refers to the python virtual environment where you installed Kansha.

``nagare-admin`` reference
--------------------------

Read http://www.nagare.org/trac/wiki/NagareAdmin.


Configuration file
------------------

Kansha features can be activated and customized with a configuration file like this:

.. code-block:: INI

    [application]
    path = app kansha
    name = kansha
    debug = off
    redirect_after_post = on
    as_root = on
    title = <<APP_TITLE>> # should be short!
    banner = <<LONG_TITLE>> # or motto/slogan or empty
    theme = <<CUSTOM_THEME_NAME>>
    favicon = # path (optional)
    activity_monitor = <<MONITOR_EMAIL>> # optional
    crypto_key = <<PASSPHRASE>> # MANDATORY!!!!
    disclaimer = # message to display on login screens, below the forms (optional)

    [database]
    debug = off
    activated = on
    uri = postgres://<<DBUSER>>:<<DBPASS>>@<<DBHOST>>:<<DBPORT>>/<<DBNAME>> # adapt to your own DBMS
    metadata = elixir:metadata
    populate = kansha.populate:populate
    # especially useful for mysql
    #pool_recycle = 3600

    [search]
    engine = sqlite
    collection = kansha
    index_folder = <<DATA_DIR>>

    [authentication]
    # built in authentication system
    [[dblogin]]
    activated = <<AUTH_DB>>
    # moderator email if needed
    moderator = <<MOD_EMAIL>> # or empty
    # automatically create an identicon for new users (on|off)
    identicons = on
    # default values to fill in the login form (useful for a demo board)
    default_username = <<DEFAULT_USERNAME>>
    default_password = <<DEFAULT_PASSWORD>>

    # authenticate with LDAP
    [[ldaplogin]]
    activated = <<AUTH_LDAP>>
    host = <<AUTH_LDAP_SERVER>>
    users_base_dn = <<AUTH_LDAP_USERS_BASE_DN>>
    schema = <<AUTH_LDAP_CLASS>>

    # authenticate with third party apps
    [[oauthlogin]]
    activated = <<AUTH_OAUTH>>

    # as many oauth providers as you wish
    [[[<<PROVIDER>>]]]
    activated = <<AUTH_OAUTH>>
    key = <<AUTH_OAUTH_KEY>>
    secret = <<AUTH_OAUTH_SECRET>>

    [locale]
    major = fr
    minor = FR

    [services]
    [[mail_sender]]
    activated = on
    host = <<MAIL_HOST>>
    port = <<MAIL_PORT>>
    default_sender = <<MAIL_SENDER>>

    [[assets_manager]]
    basedir = <<DATA_DIR>>/assets
    baseurl = /kansha/services
    max_size = 20480

    [logging]

    [[logger]]
    level=INFO

    [[handler]]
    class=logging.handlers.RotatingFileHandler
    args="('<<DATA_DIR>>/logs/<<LOG_FILE>>', 'a', 10485760, 8, 'UTF-8')"


Just replace the <<PLACEHOLDERS>> with your actual values.

For your convenience, you can generate a configuration template into your current directory::

    $ <VENV_DIR>/bin/kansha-admin save-config

The template is ``kansha.cfg``. Edit it as you need. Ensure the folders you set for logs, assets… do exist.

To manage and run Kansha with your own custom configuration::

    $ <VENV_DIR>/bin/nagare-admin create-db /path/to/your/kansha.cfg
    $ <VENV_DIR>/bin/kansha-admin alembic-stamp head /path/to/your/kansha.cfg
    $ <VENV_DIR>/bin/kansha-admin create-index /path/to/your/kansha.cfg
    $ <VENV_DIR>/bin/nagare-admin serve /path/to/your/kansha.cfg


The different sections are detailled below.

.. _application:

Application
-----------

Here you configure the base application.

path
    Reference to the root component factory of the application (don't edit!).

name
    URL prefix of the application (``/name/…``).

as_root
    If ``on``, the application is also available without URL prefix, directly as root URL.

debug
    If ``on``, display the web debug page when an exception occurs. The ``nagare[debug]`` extra must be installed. Never activate on a production site!

redirect_after_post
    If ``on``, every POST is followed by a GET thanks to a redirect. That way, visitors can safely use the *back* button on their browsers.

title
    Short name for your instance, displayed in various places of the interface. It is the identity of your site. Keep it short (less than 10 chars).

banner
    Longer title for your site, kind of motto or slogan. It is displayed below the logo on the login page.

theme
    Name of the theme you want to use, a default one is bundled with Kansha and is named "kansha_flat".

favicon
    Path to a favicon file that will be applied to your site.

activity_monitor
    Email address or nothing. If an email address is provided, activity reports will be sent to it regularly. See :ref:`periodic_tasks`.

crypto_key
    **Required**: this key is used to encrypt cookies. You must change it to secure your site. Put in an hundred random chars (ask a typing monkey).

disclaimer
    This message is displayed below the login form. You can leave it empty of course.


Database
--------

Kansha data are stored in an SQL database. Thanks to SQLAlchemy, we support all the major databases of the market.

Depending on the DBMS you use, you may need to create the target database first.

Configuration options:

uri
    SQL Alchemy URI. See http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#supported-databases

pool_recycle
    If you are using MySQL as your database backend, you may need to set this option if the mysql configuration sets an automatic disconnection.

Let the other options at their default values.

Note for Postgresql (recommended DBMS for production sites) users:

 *  install the needed dependencies::

        $ <VENV_DIR>/bin/easy_install kansha[postgres]

Note for MySQL users:

 * install the needed dependencies::

        $ <VENV_DIR>/bin/easy_install kansha[mysql]


Search
------

You can choose one out of two search backends for the moment: SQLite or ElasticSearch.
They both work independently from the database you chose to store your data in.

The SQLite backend is quite fast and capable but is only able to do prefix searches. More demanding sites may require ElasticSearch, or you may already have a running cluster on your network.

SQLite backend
^^^^^^^^^^^^^^

This backend is based upon SQLite FTS tables.
You need sqlite 3.8.0 or newer. Yet, the search engine can still work with limited functionality down to sqlite 3.7.7.
As far as Kansha is concerned, it should not make any difference, since it doesn't use the missing features (for the moment).

Configuration options:

engine
    sqlite

index
    The base name of the index file (will be created).

index_folder
    Where to put the index file (must exist).


ElasticSearch backend
^^^^^^^^^^^^^^^^^^^^^

Requires ElasticSearch v2.3.0 or above.

You need to install the python driver first::

    $ <VENV_DIR>/bin/easy_install kansha[elastic]

Configuration options:

engine
    elastic

index
    the name of the index on the ElasticSearch cluster (will be created).

host
    Optional

port
    Optional


Authentication
--------------

You can use up to four different systems, as modules, to authenticate your users in Kansha. You can activate as many modules as you want (at least one).

Module ``dbauth``
^^^^^^^^^^^^^^^^^

Database authentication. Users must register first via the web interface.

Configuration options:

activated
    Whether to activate this module.

identicons
    Whether a unique avatar should be created for each new user instead of the default anonymous one (``on`` / ``off``).

moderator
    If present, must be an email address. This activates moderation and all registration requests are fowarded to the moderator for approval. Otherwise, registration is free for humans. A CAPTCHA prevents robots from submitting.


Module ``ldapauth``
^^^^^^^^^^^^^^^^^^^

Use this module to authenticate your users against an LDAP or Active Directory database.

You will need to install some additional packages::

        $ <VENV_DIR>/bin/easy_install kansha[ldap]

Configuration options:

activated
    Activate only if you have some LDAP Directory.

host
    name or address of the LDAP server.

port
    (optional) port to connect to.

users_base_dn
    The base DN your users are under.

schema
    The driver to use depending on your schema:

    * ``kansha.authentication.ldap.ldap_auth:NngLDAPAuth`` for InetOrgPerson
    * ``kansha.authentication.ldap.ldap_auth:ADLDAPAuth`` for Active Directory

**Note**: the ``kansha.authentication.ldap.ldap_auth:NngLDAPAuth`` driver expects the fields  "displayName" and "mail" to be set.

Module ``oauth``
^^^^^^^^^^^^^^^^

This governs the OAuth based authentication system. You need to activate it if you wish to let your users connect with their accounts on third party sites or applications.

For that, you configure a provider as a subsection of ``oauth``.

The name of the subsection is the provider name (list below) in lowercase. Each subsection has the following configuration parameters:

activated
    ``on`` or ``off``.

key
    Write here the API key of the service you intend to use (you have to register with the service first to get one)

secret
    Write here the secret that authenticates your site by the service you intend to use (you have to register with the service first to get one)


The availble providers are:

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

Example:

.. code-block:: INI

    [[oauthlogin]]
    activated = on

    [[[google]]]
    activated = on
    key = xxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com
    secret = XXXXXXXXXXXXXXXXXXXXXXXX

    [[[facebook]]]
    activated = on
    key = 0000000000000000000
    secret = XXXXXXXXXXXXXXXXXXXXXXXX



.. _mail:

Send Mail
---------

All notifications are sent by mail, so you'd better configure an outgoing SMTP server.

host
    SMTP server to use.

port
    The port the server listens on.

default_sender
    The sender address that will appear on all the messages sent by your site.


Asset Manager
-------------

You can attach files and images to cards, so you need to set where they will be stored on disk.

basedir
    The folder where to store uploaded files.

max_size
    The maximum allowed size of uploaded files, in kilobytes.

Locale
------

major
    Default language for your site, two-letter ISO language code.

minor
    Default region for your site, two-letter ISO country code.

Logging
-------

This is the configuration for the standard  python logger. See https://docs.python.org/2/library/logging.config.html#configuration-file-format for a complete explanation.

At a minimum, configure the path to the log file and the logging level.




