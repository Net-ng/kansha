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

Installation
------------

As in the quickstart guide, follow the installation steps from :ref:`python_install`.

You also need to install:

* the database you want to use;
* memcached;
* your favorite web server with FCGI support;
* and if you choose to, ElasticSearch.

You can use the default configurations for memcached and ElasticSearch.

Then configure Kansha (:ref:`configuration_guide`).

In any case, you always need to::

    $ <STACKLESS_DIR>/bin/nagare-admin create-db --no-populate </path/to/your/kansha.cfg>
    $ <STACKLESS_DIR>/bin/nagare-admin create-index </path/to/your/kansha.cfg>

When you **first** deploy.

The ``--no-populate`` option ensures that the default users (*user1*, *user2* and *user3*) are not created.

Deployment behind a web server
------------------------------

To deploy Kansha behind a web server, we use a Fast CGI (FCGI) adapter and a memcached server to allow communication between processes.

The steps are:

1. install, configure and start memcached;
2. configure kansha to start FCGI processes;
3. install, configure and start your favorite web server with FCGI connectivity to Kansha processes.

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
    min_compress_len = 1
    reset = true

Set the <<PLACEHOLDERS>> as appropriate.

Optimize how static contents are served
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

nagare-admin create-rules

Using a supervisor
^^^^^^^^^^^^^^^^^^

Optional, to be written…


.. _periodic_tasks:

Periodic tasks
--------------

Kansha emits notifications users can subscribe to. In order for those notifications to be sent, you have to call a batch task regularly::

    nagare-admin batch <<PATHTOCONFFILE>> kansha/batch/send_notifications.py <<TIMESPAN>> <<APPURL>>

Where the <<PLACEHOLDERS>> are correctly replaced by, respectively:

* the path to the configuration file of Kansha;
* the timespan covered by the reports;
* the url of the application.

You can locate the ``send_notifications.py`` file in your python installation (``site-packages``).

Place this command in a crontab and check that the timespan matches the time interval between each run.


Upgrading a production site
---------------------------

We mean *upgrading Kansha*.

First activate the virtual environment from which you are running Kansha and just type::

    $ easy_install --upgrade kansha

Or, if you want a specific version instead of the latest stable (replace X, Y and Z with the actual numbers)::

    $ easy_install kansha==X.Y.Z

Migrate database and/or indexes (more to come).

Now restart Kansha.
