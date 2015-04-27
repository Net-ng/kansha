KANSHA
=====

Kansha is a web application to manage and share collaborative pinboards.

Kansha works with Firefox, Chrome, Internet Explorer 9 and above, Safari 7 and above, with the mouse. Kansha is currently not compatible with touch devices.


Quickstart
----------

Installation
~~~~~~~~~~~~

Nagare, the framework used by Kansha, needs stackless python 2.7 to run.

You can install stackless python 2.7 from there:
http://www.stackless.com/wiki/Download

Then, we recommend using a virtual environment for deploying Kansha:
https://virtualenv.pypa.io/en/latest/

Finally, in your activated virtual environment, type::

  pip install -f http://www.nagare.org/snapshots/  --allow-all-external --trusted-host www.nagare.org --allow-unverified PEAK-Rules kansha


Run
~~~

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


See the ``doc/`` folder in the source for detailled documentation about configuration and deployment on production servers.
