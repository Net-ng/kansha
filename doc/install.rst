Installing Kansha
=================

Quickstart
----------

Installation
^^^^^^^^^^^^

Nagare, the framework used by Kansha, needs `Stackless Python`_ (version 2.7.X) to run.

In order to install it via the sources, complete the following commands::

    $ mkdir <STACKLESS_DIR>
    $ wget http://www.stackless.com/binaries/stackless-278-export.tar.bz2
    $ tar xf stackless-278-export.tar.bz2
    $ ./configure --prefix=<STACKLESS_DIR> && make -j3 all && make install

More details in `its documentation`_.

.. _Stackless Python: http://www.stackless.com

.. _its documentation: http://www.stackless.com/wiki

Then, we recommend using a virtual environment for deploying Kansha.
To install `virtualenv` within your fresh Stackless Python, you can execute the following commands::

    $ wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | <STACKLESS_DIR>/bin/python
    $ <STACKLESS_DIR>/bin/easy_install virtualenv

To create a virtual environment::

    $ <STACKLESS_DIR>/bin/virtualenv <VENV_DIR>

To activate that new environment::

    $ source <VENV_DIR>/bin/activate

More details at https://virtualenv.pypa.io/en/latest/

Finally, when your virtual environment is active in your shell, type::

  easy_install --find-links http://www.nagare.org/snapshots/ kansha

**Note to PIP users**: you currently can not use ``pip`` to install `kansha` because some data files and folders would be spread all over ``site-package``.
The command ``easy_install`` puts each distribution into its own folder.

Run
^^^

To get quickly up and running, let's use the built-in web server, database and search engine with the default configuration.

1. First initialize the database (first run only)::

    nagare-admin create-db kansha

2. Build the search indexes (can be repeated anytime)::

    nagare-admin create-index kansha

3. Launch::

    nagare-admin serve kansha

Now kansha is listening. Just point your browser to http://localhost:8080 and enjoy!


Production setup
----------------

The built-in server, database and search engine are very convenient for testing, but they are not recommended for production setups.

Fortunately, you can run Kansha with:

* any database supported by SQLAlchemy (complete list at http://docs.sqlalchemy.org/en/rel_0_9/dialects/index.html);
* behind any webserver which supports Fast CGI (FCGI);
* with ElasticSearch as search engine.

Configuration file
^^^^^^^^^^^^^^^^^^

Kansha features can be activated and customized with a configuration file like this:

.. code-block:: INI

    [application]
    path = app kansha
    name = kansha
    debug = off
    redirect_after_post = on
    as_root = on
    title = <<APP_TITLE>>
    custom_css = <<CUSTOM_CSS>>  # path or empty
    templates = <<JSON_BOARD_TEMPLATES>> # path to dir or empty
    activity_monitor = <<MONITOR_EMAIL>> # optional
    crypto_key = <<PASSPHRASE>> # MANDATORY!!!!

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
^^^^^^^^^^^^^^

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
^^^^^^^^

Kansha uses SQLAlchemy to connect to databases. Adapt the URI in the configuration file to your own setup. Depending on the DBMS you use, you may need to create the target database first.
For documentation on how to write such URIs, see http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html#database-urls.

Note for Postgresql (recommended) users:

 *  install the needed dependencies::

    easy_install kansha[postgres]

Note for MySQL users:

 * install the needed dependencies::

    easy_install kansha[mysql]

 * in the configuration file, the option ``pool_recycle`` has to be set to a value consistent with the ``wait_timeout`` system variable of MySQL.

Search engine
^^^^^^^^^^^^^

We currently support two search engine plugins for Kansha:

sqlite
    SQLite FTS based plugin. Configuration options are:

    * collection (the name of the index)
    * index_folder (folder where the index is stored)

elastic
    ElasticSearch based plugin. Configuration options are:

    * collection (name of the index)
    * host
    * port

In order to use ElasticSearch, install the needed dependencies::

    easy_install kansha[elastic]

Deployment behind a web server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To deploy Kansha behind a web server, we use a Fast CGI (FCGI) adapter and a memcached server to allow communication between processes.

The steps are:

1. install, configure and start memcached;
2. configure kansha to start FCGI processes;
3. install, configure and start your favorite web server with FCGI connectivity to Kansha processes.

Configure Kansha for FCGI
"""""""""""""""""""""""""

Append these directives to your configuration file:

.. code-block:: INI

    [publisher]
    type = fastcgi
    host = <<FASTCGI_HOST_KANSHA>>
    port = <<FASTCGI_PORT_KANSHA>>
    debug = off
    minSpare = <<FASTCGI_MINSPARE>>
    maxSpare = <<FASTCGI_MAXSPARE>>
    maxChildren = <<FASTCGI_MAXCHILDREN>>

    [reloader]
    activated = off
    interval = 1

    [sessions]
    type = memcache
    host = <<MEMCACHE_HOST>>
    port = <<MEMCACHE_PORT>>
    min_compress_len = 1
    reset = true

Set the <<PLACEHOLDERS>> as appropriate.

Periodic tasks
^^^^^^^^^^^^^^

Kansha emits notifications users can subscribe to. In order for those notifications to be sent, you have to call a batch task regularly::

    nagare-admin batch <<PATHTOCONFFILE>> kansha/batch/send_notifications.py <<TIMESPAN>> <<APPURL>>

Where the <<PLACEHOLDERS>> are correctly replaced by, respectively:

* the path to the configuration file of Kansha;
* the timespan covered by the reports;
* the url of the application.

You can locate the ``send_notifications.py`` file in your python installation (``site-packages``).

Place this command in a crontab and check that the timespan matches the time interval between each run.
