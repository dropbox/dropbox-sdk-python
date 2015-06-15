Dropbox for Python
==================

A Python SDK for integrating with the Dropbox API v2.

Setup
-----

You can install this package from the root directory by running::

    $ python setup.py install

After installation, to get started, open a Python console::

    >>> import dropbox
    >>> dbx = dropbox.Dropbox(YOUR_ACCESS_TOKEN)
    >>> dbx.users_get_current_acccount()

Creating an Application
-----------------------

You need to create an Dropbox Application to make API requests.

- Go to https://dropbox.com/developers/apps.

Obtaining a User Token
----------------------

All requests need to be made with a user token. To get started, once you've
created an app, you can go to the app's console and generate an access token
for your own Dropbox account.

Examples
--------

An example, ``updown.py``, can be found in the examples directory, which
demonstrates how to sync a local directory with a Dropbox.

Documentation
-------------

Documentation can be compiled by running ``make html`` from the ``docs``
folder. After compilation, open ``docs/_build/html/index.html``.

