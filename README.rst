.. image:: https://cfl.dropboxstatic.com/static/images/sdk/python_banner.png
    :target: https://github.com/dropbox/dropbox-sdk-python

.. image:: https://img.shields.io/pypi/pyversions/dropbox.svg
    :target: https://pypi.python.org/pypi/dropbox

.. image:: https://img.shields.io/pypi/v/dropbox.svg
    :target: https://pypi.python.org/pypi/dropbox

.. image:: https://codecov.io/gh/dropbox/dropbox-sdk-python/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/dropbox/dropbox-sdk-python

The offical Dropbox SDK for Python.

Documentation can be found on `Read The Docs`_.

Installation
============

Create an app via the `Developer Console`_.

Install via `pip <https://pip.pypa.io/>`_:

.. code-block:: console

    $ pip install dropbox

Install from source:

.. code-block:: console

    $ git clone git://github.com/dropbox/dropbox-sdk-python.git
    $ cd dropbox-sdk-python
    $ python setup.py install

After installation, follow one of our `Examples`_ or read the documentation on `Read The Docs`_.

You can also view our `OAuth Guide`_.

Examples
========

We provide `Examples`_ to help get you started with a lot of the basic functionality in the SDK.

- **OAuth**
    - `Commandline OAuth Basic <https://github.com/dropbox/dropbox-sdk-python/blob/main/example/oauth/commandline-oauth.py>`_ - Shows a simple example of commandline oauth (no redirect).
    - `Commandline OAuth Scopes <https://github.com/dropbox/dropbox-sdk-python/blob/main/example/oauth/commandline-oauth-scopes.py>`_ - Shows a simple example of commandline oauth using scopes.
    - `Commandline OAuth PKCE <https://github.com/dropbox/dropbox-sdk-python/blob/main/example/oauth/commandline-oauth-pkce.py>`_ - Shows a simple example of commandline oauth using PKCE.
- **Other Examples**
    - `Updown <https://github.com/dropbox/dropbox-sdk-python/blob/main/example/updown.py>`_ - Sample application that uploads the contents of your ``Downloads`` folder to Dropbox.
    - `Backup and Restore <https://github.com/dropbox/dropbox-sdk-python/tree/main/example/back-up-and-restore>`_ - Sample application that shows how you can backup a file and restore previous versions if the file was modified/corrupted in any way.

Getting Help
============

If you find a bug, please see `CONTRIBUTING.md`_ for information on how to report it.

If you need help that is not specific to this SDK, please reach out to `Dropbox Support`_.

License
=======

This SDK is distributed under the MIT license, please see `LICENSE`_ for more information.

.. _logo: {logo_link}
.. _repo: https://github.com/dropbox/dropbox-sdk-python
.. _`Read The Docs`: http://dropbox-sdk-python.readthedocs.org
.. _`Examples`: https://github.com/dropbox/dropbox-sdk-python/tree/main/example
.. _LICENSE: https://github.com/dropbox/dropbox-sdk-python/blob/main/LICENSE
.. _CONTRIBUTING.md: https://github.com/dropbox/dropbox-sdk-python/blob/main/CONTRIBUTING.md
.. _Developer Console: https://dropbox.com/developers/apps
.. _OAuth Guide: https://www.dropbox.com/lp/developers/reference/oauth-guide
.. _`Dropbox Support`: https://www.dropbox.com/developers/contact