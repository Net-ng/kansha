.. _develenv:

Development setup
=================

How to setup your environment and install Kansha from GitHub for development.

Beside the :ref:`requirements`, you need to have :program:`git` installed.
You should already be familiar with :program:`git` and GitHub.
If that's not the case, check https://help.github.com/articles/good-resources-for-learning-git-and-github/.

The following instructions apply to UNIX-like systems, like Linux or MacOS X.

Install Stackless Python and Virtualenv
---------------------------------------

Nagare, the framework used by Kansha, needs `Stackless Python`_ (version 2.7.X) to run.

Unfortunatly, none of the major Linux distributions offer packages for Stackless, so you have to build it from sources.

In order to install it via the sources, first ensure you have the :ref:`prerequisite system dependencies <requirements>`, then complete the following commands::

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

Install Kansha for development
------------------------------

First, create a stackless virtual environment so your development environment remain isolated::

    $ <STACKLESS_DIR>/bin/virtualenv <VENV_DIR>

<VENV_DIR> is whereever you want your virtual environment be created. Note that we won't be working in that directory directly, so it can be a hidden one.

Fork the Kansha project on `GitHub <https://github.com/Net-ng/kansha>`_.

Clone your project locally. Now you have a ``kansha`` folder (<KANSHA_DIR> in the following). That's where the actual development will take place.

Activate the virtual environment you created above::

    $ source <VENV_DIR>/bin/activate

Then install Kansha in development mode::

    $ cd <KANSHA_DIR>
    $ python setup.py develop

The last command installs kansha in the virtual environment *in place*.
That is, any modification done to the files in :file:`kansha/kansha` will be available immediatly, without re-installing.

Finally, install all the optional dependencies of Kansha::

    $ pip install kansha[test]
    $ pip install kansha[htmldocs]
    $ pip install kansha[ldap]
    $ pip install kansha[postgres]
    $ pip install kansha[mysql]
    $ pip install kansha[elastic]

Configure Kansha
----------------

In the :file:`conf` directory, copy :file:`kansha.cfg` to :file:`kansha.local.cfg` and edit the latter to fit your system.

Test run
--------

For developing, let's use the built-in web server, database and search engine with the custom configuration.

Place yourself at the root of the project (<KANSHA_DIR>). The virtual environment is still activated in your shell (look at the prompt); if not, activate it.

1. First, initialize the database (first run only)::

    $ nagare-admin create-db conf/kansha.local.cfg

2. Build the search indexes (can be safely repeated anytime, only needed at firt run actually)::

    $ nagare-admin create-index conf/kansha.local.cfg

3. Launch::

    $ nagare-admin serve conf/kansha.local.cfg --reload

Now kansha is listening. Just point your browser to http://localhost:8080 and check.

The ``--reload`` switch is handy for development, as the server then reloads kansha whenever a python file is modified.

Later, each time you'll want to run Kansha in development mode,remember these steps::

    $ cd <KANSHA_DIR>
    $ source <VENV_DIR>/bin/activate
    $ nagare-admin serve conf/kansha.local.cfg --reload

Development cycle
-----------------

Now that your environment is ready and kansha is running is development mode, let's hack!

Generic workflow:

1. Develop;
2. translate (if appliable);
3. document;
4. write unit tests for internal funtionality and API (*for the latter, write the tests first, then develop*);
5. test;
6. repeat from 1. until your tests (automatic and/or manual) pass;
7. commit with appropriate message;
8. go to 1 until your work is done;
9. push;
10. submit a pull request on github.

Specific recommendations and workflows are described in theses sections:

* :ref:`contribute_doc`
* :ref:`contribute_trans`
* :ref:`contribute_code`


It's highly recommended that you subscribe to the mailing list: http://groups.google.com/group/kansha-users