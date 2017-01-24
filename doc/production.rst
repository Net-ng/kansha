.. _production_setup:

Production setup
================

The built-in server, database and search engine are very convenient for testing,
but they are not recommended for production sites
(*Well, in fact, the default search engine is quite capable; do some benchmarks to decide*).

Fortunately, you can run Kansha with:

* any database supported by SQLAlchemy (complete list at http://docs.sqlalchemy.org/en/rel_0_9/dialects/index.html);
* behind any webserver which supports Fast CGI (FCGI);
* different authentication backends;
* with ElasticSearch as search engine.

For instructions on how to configure Kansha and for detailled explanations of each option, please read the :ref:`configuration_guide`.

In this section, we concentrate on how to deploy Kansha as a multiprocess application backend behind a web server.

In the following, <VENV_DIR> is the path to the python virtual environment you've installed Kansha in.

Installation
------------

As in the quickstart guide, follow the installation steps from :ref:`python_install`.

You also need to install:

* the database you want to use;
* memcached;
* your favorite web server with FCGI support;
* and if you choose to, ElasticSearch.

You can run memcached and ElasticSearch with their default configurations.

Then configure Kansha (:ref:`configuration_guide`).

In any case, you always need to::

    $ <VENV_DIR>/bin/nagare-admin create-db </path/to/your/kansha.cfg>
    $ <VENV_DIR>/bin/kansha-admin alembic-stamp head </path/to/your/kansha.cfg>
    $ <VENV_DIR>/bin/kansha-admin create-index </path/to/your/kansha.cfg>

When you **first** deploy.

Deployment behind a web server
------------------------------

To deploy Kansha behind a web server, we use a Fast CGI (FCGI) adapter and a memcached server to allow communication between processes.

The steps are:

1. install, configure and start memcached;
2. configure kansha to start FCGI processes;
3. install, configure and start your favorite web server with FCGI connectivity to Kansha processes;
4. start Kansha.

Configure Kansha for FCGI
^^^^^^^^^^^^^^^^^^^^^^^^^

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
    min_compress_len = 100000
    reset = true

Or, if you run the web server on the same machine as Kansha, you can use unix sockets:

.. code-block:: INI

    [publisher]
    type = fastcgi
    socket = <<SOCKET_PATH>>
    umask = <<SOCKET_MASK>>
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
    min_compress_len = 100000
    reset = true


Set the <<PLACEHOLDERS>> as appropriate.

A sample configuration you can start with (assuming memcached is running with defaults and you use sockets):

.. code-block:: INI

    [publisher]
    type = fastcgi
    socket = /path/to/the/socket/you/want
    debug = off
    minSpare = 2
    maxSpare = 4
    maxChildren = 10

    [reloader]
    activated = off
    interval = 1

    [sessions]
    type = memcache
    host = localhost
    port = 11211
    min_compress_len = 100000
    reset = true


All options are documented in this `section of the Nagare documentation <http://www.nagare.org/trac/wiki/PublisherConfiguration>`_.

Optimize how static contents are served
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Your web server is better at serving static content than Kansha, so you'd better configure it to serve the static resources itself and pass the other requests to the Kansha backend.

If you are using Apache, Nginx or Lighttpd, you'll find the detailled instructions in the `deployment section of the Nagare manual <http://www.nagare.org/trac/wiki/ApplicationDeployment>`_.


Start Kansha
^^^^^^^^^^^^

Once you have configured the FCGI publisher, you can start Kansha as usual::

    $ <VENV_DIR>/bin/nagare-admin serve </path/to/your/kansha.cfg>

That command starts the backend FCGI processes.


Using a supervisor
^^^^^^^^^^^^^^^^^^

Optional, but recommended, see `Handling the FastCGI processes <http://www.nagare.org/trac/wiki/ApplicationDeployment#handling-the-fastcgi-processes>`_ in the Nagare manual.


.. _periodic_tasks:

Periodic tasks
--------------

Kansha emits notifications users can subscribe to. In order for those notifications to be sent, you have to call a batch task regularly::

    $ <VENV_DIR>/bin/nagare-admin batch <<PATHTOCONFFILE>> kansha/batch/send_notifications.py <<TIMESPAN>> <<APPURL>>

Where the <<PLACEHOLDERS>> are correctly replaced by, respectively:

* the path to the configuration file of Kansha;
* the timespan covered by the reports (in hours);
* the url of the application.

You can locate the ``send_notifications.py`` file in your python virtual environment (:file:`<VENV_DIR>/lib/python2.7/site-packages/kansha/batch/`).

Place this command in a crontab and check that the timespan matches the time interval between each run.

Of course, that assumes you have previously configured an outgoing SMTP server in the :ref:`mail` section of the configuration file.

.. _upgrading:

Upgrading a production site
---------------------------

We mean *upgrading Kansha* while keeping your data.

Just type::

    $ <VENV_DIR>/bin/easy_install --upgrade kansha
    $ <VENV_DIR>/bin/kansha-admin alembic-upgrade head </path/to/your/kansha.cfg>
    $ <VENV_DIR>/bin/kansha-admin create-index </path/to/your/kansha.cfg>

Or, if you want a specific version instead of the latest release (replace X, Y and Z with the actual numbers)::

    $ <VENV_DIR>/bin/easy_install kansha==X.Y.Z

Migrate database and/or indexes (more to come).

Update the rewrite rules for static resources.

Now restart Kansha.
