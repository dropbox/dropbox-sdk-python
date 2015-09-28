Dropbox for Python
==================

A Python SDK for integrating with the Dropbox API v2. Compatible with Python
2.7 and 3.4+. Documentation is available on `Read the Docs
<http://dropbox-sdk-python.readthedocs.org/>`_.

Setup
-----

You can install this package from the root directory by running::

    $ python setup.py install

After installation, to get started, open a Python console::

    >>> import dropbox
    >>> dbx = dropbox.Dropbox("YOUR_ACCESS_TOKEN")
    >>> dbx.users_get_current_acccount()

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

Upgrading from v1
-----------------

To ease the transition to the new API and SDK, you can still use the old
``dropbox.client.DropboxClient`` class. In fact, v2 and v1 can be used
simultaneously.  Support for the old client will be dropped once the new SDK is
at functional parity.

Running tests
-------------

We use the `tox <https://tox.readthedocs.org/>`_ package to run tests in Python
2 and 3. To install, use `pip install tox`. Once installed, run `tox` from the
root directory. You'll need to specify a working Dropbox OAuth2 token::

    $ DROPBOX_TOKEN=YOUR_TOKEN tox

