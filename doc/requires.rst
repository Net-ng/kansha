.. _requirements:

System dependencies
===================

These are the sytem dependencies needed to compile Stackless Python 2.7 and some of python extensions used by Kansha.

Debian based Linux distributions
--------------------------------

(Ubuntu…)

In a terminal type::

    $ sudo apt-get build-dep python2.7
    $ sudo apt-get install gcc make libxml2-dev libxslt-dev libjpeg8-dev libopenjpeg-dev libwebp-dev libmysqld-dev libldap2-dev libsasl2-dev libpcre3-dev libtiff5-dev libpq-dev libsqlite3-dev


If you can't do it yourself, ask your system administrator.

RPM based Linux distributions
-----------------------------

(CentOS, Fedora…)

In a terminal type::

    $ yum groupinstall -y 'development tools'
    $ yum -y install git curl gpg bzip2 install gcc make file gettext readline-devel zlib-devel sqlite-devel ncurses-devel bzip2-devel openssl-devel gdbm-devel db4-devel libffi-devel libxml2-devel libxslt-devel libjpeg-devel mysql-devel openldap-devel libgsasl-devel pcre-devel libtiff-devel sqlite postgresql-devel

If you can't do it yourself, ask your system administrator.

Other Linux distributions
-------------------------

Adapt the instructions above to your particular Linux installation or ask your system administrator.

MacOS X
-------

Please contribute to this section!