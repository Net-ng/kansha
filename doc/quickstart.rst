Quickstart guide
================

There are two ways to install the latest stable release of Kansha:

#. By using Docker and the public image we maintain on the Docker Registry;
#. Or by directly installing the python package on your computer.

The second method is the preferred one for production sites (for now). You can also install older stable versions with that method.


Docker image
------------

This section assumes your are already familiar with Docker,
you have a running Docker daemon somewhere and your `docker` command is correctly set up.

For the impatient
^^^^^^^^^^^^^^^^^

Just type::

    $ docker run -p 8080:8080 netng/kansha

Now point your browser to  http://localhost:8080 and enjoy!

*If you are using Boot2docker or Docker Machine (Windows/MacOS), replace* ``localhost`` *above by the IP address of your virtual machine.*

Update your local image
^^^^^^^^^^^^^^^^^^^^^^^

If we release a new image after you executed the above command,
you won't be able to run it unless you explicitly update your local image::

    $  docker pull netng/kansha

The provided image is not usable (yet) for production sites, but you can build your own.
For that purpose, we provide the Dockerfile used to produce the public image on `GitHub <https://github.com/Net-ng/kansha/blob/master/Dockerfile>`_.
Then you have to adapt it. See :ref:`production_setup` for details.


.. _python_install:

Python package
--------------

The following instructions apply to UNIX-like systems, like Linux or MacOS X.

Installation
^^^^^^^^^^^^

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

To create a virtual environment::

    $ <STACKLESS_DIR>/bin/virtualenv <VENV_DIR>

To activate that new environment::

    $ source <VENV_DIR>/bin/activate

More details at https://virtualenv.pypa.io/en/latest/

Finally, when your virtual environment is active in your shell, type::

    $ easy_install --find-links=http://www.nagare.org/snapshots/  kansha

.. pip install --allow-external PEAK-Rules  --allow-unverified PEAK-Rules --find-links=http://www.nagare.org/snapshots/ --trusted-host www.nagare.org kansha

**Note to PIP users**: you currently should not use :command:`pip` to install :program:`Kansha` because some data files and folders would be spread all over ``site-packages``.
The command :command:`easy_install` puts each distribution into its own folder, preventing conflicts.

**easy_install caveat**: :command:`easy_install` ignores completely `semantic versioning <https://www.python.org/dev/peps/pep-0440/>`_ and may install the lastest development release instead of the latest stable. In that case, you'd better specify the version you want explicitly, for example::

    $ easy_install --find-links=http://www.nagare.org/snapshots/  kansha==1.0.4


Test run
^^^^^^^^

To get quickly up and running, let's use the built-in web server, database and search engine with the default configuration.

1. First, initialize the database (first run only)::

    $ nagare-admin create-db kansha
    $ kansha-admin alembic-stamp head
    $ kansha-admin create-demo  # optional, create demo users and contents

2. Build the search indexes (can be safely repeated anytime)::

    $ kansha-admin create-index

3. Launch::

    $ nagare-admin serve kansha

Now kansha is listening. Just point your browser to http://localhost:8080 and enjoy!

For production sites, we recommend you use an external web server, see :ref:`production_setup`.

Upgrading
^^^^^^^^^

Upgrading Kansha without loosing data is very easy::

    $ easy_install --upgrade kansha
    $ kansha-admin alembic-upgrade head
    $ kansha-admin create-index

And then restart.