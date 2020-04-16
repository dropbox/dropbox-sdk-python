Contributing
============

Contributions are more than welcome and we encourage people to help us make our SDKs better.


Documentation
-------------

Documentation can be compiled by running ``make html`` from the ``docs``
folder. After compilation, open ``docs/_build/html/index.html``. Alternatively,
you can read a hosted version from `Read the Docs <https://dropbox-sdk-python.readthedocs.org/en/stable/>`_.

Updating API specification
--------------------------

A good amount of this SDK is generated using `Stone
<https://www.github.com/dropbox/stone>`_. We use git submodules to pin to a
specific version of `Stone` since it's under active development, and we also
pin to a version of our `API spec
<https://www.github.com/dropbox/dropbox-api-spec>`_.

To prepare the repo for generation, run these commands after cloning:

.. code-block:: console

    $ git submodule init
    $ git submodule update

You can run ``git pull`` within these sub repositories to update the pinned
version.

Now, run the included script:

.. code-block:: console

    $ ./generate_base_client.py

Testing
-------

We use the `tox <https://tox.readthedocs.org/>`_ package to run tests in Python
2 and 3. To install, use :code:`pip install tox`. Once installed, run `tox` from the
root directory. You'll need to specify a working Dropbox OAuth2 token:

.. code-block:: console

    $ DROPBOX_TOKEN=YOUR_TOKEN tox -- -k "'not test_team'"

Note that we skip ``test_team`` which requires a team token with `Member File Access
<https://www.dropbox.com/developers/documentation/http/teams#teams-member-file-access>`_.
To test this functionality, specify a ``DROPBOX_TEAM_TOKEN`` environment
variable.

.. code-block:: console

    $ DROPBOX_TOKEN=... DROPBOX_TEAM_TOKEN=... tox