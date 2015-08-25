How to contribute to Kansha
===========================

You don't have to be a developer to help Kansha get better.
You can contribute in many ways depending on your skills and preferences.

Spread the word!
----------------

If you enjoy Kansha, share it! It's open source and free, even for companies. Don't hesitate to promote it inside your organization or working team. It's a profitable tool for collaborators on a project.


.. _feedback:

Give some feedback
------------------

Bug reports
^^^^^^^^^^^

Help us improving Kansha by reporting the bugs or unexpected behaviors you may encounter, by following the steps below.

Can you reproduce the issue?
    Try to reproduce your bug using a recent version of the software, to see whether it has already been fixed. The easiest way to test the latest stable version of Kansha is on the `demo <http://demo.kansha.org>`_.

Has someone else already reported the issue?
    Use the search box on `GitHub Issues`_ to see if your bug has already been reported. If it is the case, you can contribute more information by commenting the issue.

Reporting a new bug.
    If you reproduce the bug and nobody has reported it already, go to `GitHub Issues`_ and there:

    #. Click on the green button "New issue".
    #. You will be asked to log in (or register) if you have not already done so.
    #. As title, enter a  short one-sentence summary that explains the problem.
    #. As comment, tell us:

       * The version of the Kansha software on which you raised the bug (visible in the footer of your home page, or of the login page).
       * Steps to reproduce: Easy-to-follow steps that will trigger the described problem. Include any special setup steps.
       * Actual results: What the application did after performing the above steps.
       * Expected results: What the application should have done, if there was no bug.
       * The web browsers or computer systems you've seen the bug on.
       * Whether the problem appears every time, only occasionally, only on certain pages, or only in specific circumstances.

    #. Apply the "bug" label.
    #. You may also attach a log file or screenshot (but make sure that no confidential data is included or shown).
    #. Submit the issue.


Recommendations:

    * Be precise.
    * Be clear: explain how to reproduce the problem, step by step, so others can reproduce the bug.
    * Include only one problem per report.


Feature requests
^^^^^^^^^^^^^^^^

Your are missing some features in Kansha? Fill a feature request!

Make sure the feature does not already exist!
    Have a look at the latest documentation on http://kansha.readthedocs.org/latest/, or play with the latest stable version of Kansha on the `demo <http://demo.kansha.org>`_.

Has someone else already requested the feature?
    Use the search box on `GitHub Issues`_ to see if your feature has already been requested. If it is the case, you can contribute to the user story by commenting the issue.

Requesting a new feature.
    If you are sure the feature does not exist yet, and that nobody has asked for it, go to `GitHub Issues`_ and there:

    #. Click on the green button "New issue".
    #. You will be asked to log in (or register) if you have not already done so.
    #. As title, enter a  short one-sentence summary that explains the expected feature.
    #. As comment, tell us:

       * A description of what you would like to achieve, and why. A `user story <https://help.rallydev.com/writing-great-user-story>`_ is an effective way of conveying this.

    #. Apply the "enhancement" label.
    #. Submit the issue.


.. _contribute_doc:

Contribute to the documention
-----------------------------

We try hard to keep the documentation accurate and up-to-date, and volunteers are welcome.

If you find typos, inaccuracies, mistakes or misleading information;
if you think some features of Kansha deserve more detailled explanations;
if you missed some tricks or tidbitts you learned the hard way later;
please contribute directly to the manual.


.. _direct_doc:

Direct contribution
^^^^^^^^^^^^^^^^^^^

First, you'll need to prepare your :ref:`develenv`.

Like many other Python projects, we use `reStructuredText <http://docutils.sourceforge.net/rst.html>`_ to write the documentation,
and `Sphinx <http://sphinx-doc.org/>`_ and `Readthedocs <https://readthedocs.org/>`_ to format it into HTML pages.

Besides `plain reST <http://sphinx-doc.org/rest.html>`_, we also make heavy use of Sphinx extended `directives <http://sphinx-doc.org/markup/index.html>`_.

The source documentation is located in :file:`<KANSHA_DIR>/doc`. To build the html version locally, just type::

    $ cd <KANSHA_DIR>/doc
    $ make html

You will then find the HTML files in :file:`<KANSHA_DIR>/doc/_build/html/`.

Documentation workflow:

1. Redact;
2. check your grammar, spelling and syntax;
3. build the HTML;
4. proofread;
5. repeat from 1. until your text is clear, complete and correct;
6. commit with appropriate message;
7. go to 1 until your work is done;
8. push;
9. submit a pull request on github.

To avoid duplicate work or conflicts, you'd better fill an issue first, to announce what you are going to do , on `GitHub Issues`_. For that, proceed as below :ref:`indirect_doc`, except you don't have to redact your contribution inside the issue. Instead, you assign it to you.


.. _indirect_doc:

Indirect contribution
^^^^^^^^^^^^^^^^^^^^^

If the workflow described above is too complicated for you, there is an alternative, yet much less effective: submit an *enhancement* issue on `GitHub Issues`_ and wait for a volunteer to implement it.

#. Click on the green button "New issue".
#. You will be asked to log in (or register) if you have not already done so.
#. As title, enter a  short one-sentence summary that explains the proposed prose.
#. As comment, you:

    * tell us whether you propose a fix or new paragraphs/sections;
    * precise where in the manual you contribution should go;
    * **redact** the part of the manual you want to add or fix.

#. Apply the "enhancement" label.
#. Submit the issue.

And, *maybe*, a direct contributor will discuss, pick and implement your request.

.. _contribute_trans:

Translate
---------

Fixing supported languages or supporting a new language (yours!) is quite easy.

Before you start, you'll need to prepare your :ref:`develenv`.

Kansha/Nagare uses `Babel <http://babel.pocoo.org/docs/>`_ for localization.


.. _fix_lang:

Fix supported languages
^^^^^^^^^^^^^^^^^^^^^^^

First, extract the messages::

    $ cd <KANSHA_DIR>
    $ python setup.py extract_messages

That command extracted all the messages of the application marked for localization into :file:`<KANSHA_DIR>/data/locale/messages.pot`.

Then, update the translation catalogs (for all languages)::

    $ python setup.py update_catalog

Now you can edit the translation file for the language of your choice.
You'll find it at :file:`<KANSHA_DIR>/data/locale/xx/LC_MESSAGES/messages.po`
where xx is the two-letter ISO code of the target language.

If you intend to edit the :file:`.po` file with a text editor, you may need to learn the `PO format <http://pology.nedohodnik.net/doc/user/en_US/ch-poformat.html>`_ first.

Otherwise, there are some PO editors out there:

* The best known is Poedit: https://poedit.net/
* For Eclipse users, the gted extension: http://www.gted.org/

When you are done editing the po file, you have to compile it before you see the result in Kansha::

    $ python setup.py compile_catalog

The command produces a MO file at :file:`<KANSHA_DIR>/data/locale/xx/LC_MESSAGES/messages.mo` for each language.

Now restart Kansha to check your translations (the ``--reload`` switch to :command:`nagare-admin serve` is not enough).

If everything is OK, you can commit the PO file **you've edited** and not the other ones that were modified as a side effect of ``update_catalog``. You commit **one** PO file at a time.

Now you can push.

Workflow summary:

1. Extract messages::

    $ python setup.py extract_messages

2. Update catalogs::

    $ python setup.py update_catalog

3. Edit a PO file in a language you master
4. Compile it::

    $ python setup.py compile_catalog

5. Restart Kansha.
6. Check the translations.
7. Repeat from 3 (always same PO file) until done.
8. Commit your PO file with an explanatory commit message.
9. Repeat from 3 for another PO file (optional).
10. Push.
11. Submit a Pull Request.


Add a new language
^^^^^^^^^^^^^^^^^^

If you want to transalte Kansha in a new language that is not already present in :file:`<KANSHA_DIR>/data/locale/`, just initialize it with::

    $ python setup.py init_catalog --locale xx

where xx is the two-letter ISO code of the target language.

From here, you can proceed as in :ref:`fix_lang`.


.. _contribute_code:

Fix bugs and code new features
------------------------------

developer setup

issue first

processes & practices (pep8, CSS formating rules, release cycle, version numbering…)

unit tests

translation, documentation

Review others' code.


.. _GitHub Issues: https://github.com/Net-ng/kansha/issues