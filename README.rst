Dropbox for Python
==================

A Python SDK for integrating with the Dropbox API v2. Compatible with Python
2.7 and 3.4+. Documentation is available on `Read the Docs
<http://dropbox-sdk-python.readthedocs.org/>`_.

Installation
------------

Install via ``pip``:

.. code-block:: bash

    $ pip install dropbox


Install from source:

.. code-block:: bash

    $ git clone git://github.com/dropbox/dropbox-sdk-python.git
    $ cd dropbox-sdk-python
    $ python setup.py install

After installation, to get started, open a Python console:

.. code-block:: python

    >>> import dropbox
    >>> dbx = dropbox.Dropbox("YOUR_ACCESS_TOKEN")
    >>> dbx.users_get_current_account()

Creating an Application
-----------------------

You need to create an Dropbox Application to make API requests.

- Go to https://dropbox.com/developers/apps.

Obtaining an Access Token
-------------------------

All requests need to be made with an OAuth 2 access token. To get started, once
you've created an app, you can go to the app's console and generate an access
token for your own Dropbox account.

Examples
--------

An example, `updown.py <example/updown.py>`_, can be found in the examples directory, which
demonstrates how to sync a local directory with a Dropbox.

Documentation
-------------

Documentation can be compiled by running ``make html`` from the ``docs``
folder. After compilation, open ``docs/_build/html/index.html``. Alternatively,
you can read a hosted version from `Read the Docs
<http://dropbox-sdk-python.readthedocs.org/>`_.

Updating API specification
--------------------------

A good amount of this SDK is generated using `Stone
<https://www.github.com/dropbox/stone>`_. We use git submodules to pin to a
specific version of `Stone` since it's under active development, and we also
pin to a version of our `API spec
<https://www.github.com/dropbox/dropbox-api-spec>`_.

To prepare the repo for generation, run these commands after cloning:

.. code-block:: bash

    $ git submodule init
    $ git submodule update

You can run ``git pull`` within these sub repositories to update the pinned
version.

Now, run the included script:

.. code-block:: bash

    $ ./generate_base_client.py

Upgrading from v1
-----------------

To ease the transition to the new API and SDK, you can still use the old
``dropbox.client.DropboxClient`` class. In fact, v2 and v1 can be used
simultaneously.  Support for the old client will be dropped once the new SDK is
at functional parity.

Testing
-------

We use the `tox <https://tox.readthedocs.org/>`_ package to run tests in Python
2 and 3. To install, use :code:`pip install tox`. Once installed, run `tox` from the
root directory. You'll need to specify a working Dropbox OAuth2 token:

.. code-block:: bash

    $ DROPBOX_TOKEN=YOUR_TOKEN tox -- -k "'not test_team'"

Note that we skip ``test_team`` which requires a team token with `Member File Access
<https://www.dropbox.com/developers/documentation/http/teams#teams-member-file-access>`_.
To test this functionality, specify a ``DROPBOX_TEAM_TOKEN`` environment
variable.

.. code-block:: bash

    $ DROPBOX_TOKEN=... DROPBOX_TEAM_TOKEN=... tox

If you only want to test the API v2 client, use:

.. code-block:: bash

    $ DROPBOX_TOKEN=... DROPBOX_TEAM_TOKEN=... tox -- -k TestDropbox
