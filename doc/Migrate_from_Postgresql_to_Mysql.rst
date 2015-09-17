Migrate from PostgreSQL to Mysql
==================================

So you have Kansha data in your PostgreSQL database and you want to migrate them to your MySQL database.

1. First upgrade Kansha and the schema on the current database.
2. Then dump the data in a file::

    pg_dump kansha -a --attribute-inserts --format p -f kansha_pg.sql

3. In the dump:

    a. Remove SET lines,
    b. Remove lines about alembic
    c. At the beginning of the file add::

        SET NAMES 'utf8';
        SET foreign_key_checks = 0;
        START TRANSACTION;

    d. At the end of the file add::

        COMMIT;
        SET foreign_key_checks = 1;

    e. Remove the lines starting with ``SELECT pg_catalog.setval`` (sed -i 's/SELECT pg_catalog.setval/-- SELECT pg_catalog.setval/g' kansha_pg.sql)
    f. Replace PosgreSQL keywords by MySQL keywords and re-escape characters::

        sed -i 's/"when"/`when`/g' kansha_pg.sql
        sed -i 's/ "column" / `column` /g' kansha_pg.sql
        sed -i 's/ "user" / user /g' kansha_pg.sql
        sed -i 's/ index/ \`index\`/g' kansha_pg.sql
        sed -i 's/true/1/g' kansha_pg.sql
        sed -i 's/false/0/g' kansha_pg.sql
        sed -i 's/"fieldname"/\`fieldname\`/g' kansha_pg.sql
        sed -i 's/\\"/\\\\"/g'  kansha_pg.sql
        sed -i 's/\\n/\\\\n/g'  kansha_pg.sql




4. On your MySQL server, create a new database for Kansha, say ``kansha`` for example and an associated user.
5. Set up the configuration file of Kansha to use the MySQL database:

    .. code-block:: INI

        [database]
        activated = on
        #uri = sqlite:///$here/../data/kansha.db
        uri = mysql+oursql://myuser:mypass@mysqldbhost/kansha
        metadata = elixir:metadata
        debug = off
        populate = kansha.populate:populate

6. Initialize the new database::

        nagare-admin create-db kansha

7. Load the data::

    mysql -u [db_user] -p [db_pass] < kansha_pg.sql

8. Recreate the search index::

    kansha-admin create-index kansha

9. Copy ``assets`` to new location if necessary.

You are now ready to start Kansha.

**Note:** to be prepared for future scheme upgrades, you have to stamp your new database with ``alembic``. See :ref:`upgrade`.


