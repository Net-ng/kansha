.. _configuration_guide:

Configuration Guide
===================

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
    custom_css = <<CUSTOM_CSS>>  # path or empty
    templates = <<JSON_BOARD_TEMPLATES>> # path to dir or empty
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

    # built in authentication system
    [dbauth]
    activated = <<AUTH_DB>>
    # moderator email if needed
    moderator = <<MOD_EMAIL>> # or empty
    # default values to fill in the login form (useful for a demo board)
    default_username = <<DEFAULT_USERNAME>>
    default_password = <<DEFAULT_PASSWORD>>

    # authenticate with LDAP
    [ldapauth]
    activated = <<AUTH_LDAP>>
    server = <<AUTH_LDAP_SERVER>>
    users_base_dn = <<AUTH_LDAP_USERS_BASE_DN>>
    cls = <<AUTH_LDAP_CLASS>>

    # authenticate with google or facebook
    [oauth]
    activated = <<AUTH_OAUTH>>

    [[google]]
    activated = <<AUTH_OAUTH_GOOGLE>>
    key = <<AUTH_OAUTH_GOOGLE_KEY>>
    secret = <<AUTH_OAUTH_GOOGLE_SECRET>>

    [[facebook]]
    activated = <<AUTH_OAUTH_FACEBOOK>>
    key = <<AUTH_OAUTH_FACEBOOK_KEY>>
    secret = <<AUTH_OAUTH_FACEBOOK_SECRET>>

    [mail]
    activated = on
    smtp_host = <<MAIL_HOST>>
    smtp_port = <<MAIL_PORT>>
    default_sender = <<MAIL_SENDER>>

    [assetsmanager]
    basedir = <<DATA_DIR>>/assets/
    max_size = 2048

    [locale]
    major = fr
    minor = FR

    [logging]

    [[logger]]
    level=INFO

    [[handler]]
    class=logging.handlers.RotatingFileHandler
    args="('<<DATA_DIR>>/logs/<<LOG_FILE>>', 'a', 10485760, 8, 'UTF-8')"


Just replace the <<PLACEHOLDERS>> with your actual values.

To manage and run Kansha with your own custom configuration::

    nagare-admin create-db path/to/your/custom.conf
    nagare-admin create-index path/to/your/custom.conf
    nagare-admin serve path/to/your/custom.conf



Authentication
--------------

You can use up to four different systems to authenticate your users in Kansha. You can activate as many authentication systems as you want.

dbauth
    Database authentication. Users must register first via the web interface. If moderation is activated with the ``moderator`` directive, all registrations must be approved.

ldapauth
    Authenticate your users against an LDAP or Active Directory database. You will need some additional packages::

        easy_install kansha[ldap]

google
    Open your application to Google account owners. Needs oauth activated.

facebook
    Open your application to facebook users. Needs oauth activated.


Database
--------

Kansha uses SQLAlchemy to connect to databases. Adapt the URI in the configuration file to your own setup. Depending on the DBMS you use, you may need to create the target database first.
For documentation on how to write such URIs, see http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#database-urls.

Note for Postgresql (recommended) users:

 *  install the needed dependencies::

        $ easy_install kansha[postgres]

Note for MySQL users:

 * install the needed dependencies::

        $ easy_install kansha[mysql]

 * in the configuration file, the option ``pool_recycle`` has to be set to a value consistent with the ``wait_timeout`` system variable of MySQL.

Search engine
-------------

We currently support two search engine plugins for Kansha:

sqlite
    SQLite FTS based plugin. Configuration options are:

    * collection (the name of the index)
    * index_folder (folder where the index is stored)

    Supported versions of sqlite: you need sqlite 3.8.0 or newer. Yet, the search engine can work with limited functionality down to sqlite 3.7.7.
    As far as Kansha is concerned, it should not make any difference, since it doesn't use the missing features (for the moment).

elastic
    ElasticSearch based plugin. Configuration options are:

    * collection (name of the index)
    * host
    * port

In order to use ElasticSearch, install the needed dependencies::

    easy_install kansha[elastic]
