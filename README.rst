**Important: Use v12.0.2 or newer of this SDK for compatibility with the Dropbox API servers. Older versions stopped working in January 2026. Please refer to this blog post for more information: https://dropbox.tech/developers/api-server-certificate-changes**

.. image:: https://cfl.dropboxstatic.com/static/images/sdk/python_banner.png
    :target: https://github.com/dropbox/dropbox-sdk-python

.. image:: https://img.shields.io/pypi/pyversions/dropbox.svg
    :target: https://pypi.python.org/pypi/dropbox

.. image:: https://img.shields.io/pypi/v/dropbox.svg
    :target: https://pypi.python.org/pypi/dropbox

.. image:: https://codecov.io/gh/dropbox/dropbox-sdk-python/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/dropbox/dropbox-sdk-python

The official Dropbox SDK for Python.

Documentation can be found on `Read The Docs`_.

Requirements
============

This SDK requires **Python 3.11 or newer**. Earlier versions of Python, including
Python 2.7 and Python 3.4 through 3.10, are not supported, as they have reached end
of life and are no longer maintained upstream.

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
    $ pip install .

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
    - `Reliable file transfer <https://github.com/dropbox/dropbox-sdk-python/blob/main/example/file_transfer.py>`_ - Downloads and uploads files with retry, progress, and content validation helpers.
    - `Backup and Restore <https://github.com/dropbox/dropbox-sdk-python/tree/main/example/back-up-and-restore>`_ - Sample application that shows how you can backup a file and restore previous versions if the file was modified/corrupted in any way.

Reusing Cached Access Tokens
===========================

``Dropbox.get_access_token_snapshot()`` and
``DropboxTeam.get_access_token_snapshot()`` read local cached credentials without
HTTP requests or refreshing. They return an immutable ``AccessTokenSnapshot``
with ``access_token`` and ``expires_at``, or ``None`` if no access token is cached.
Expiration is a ``datetime`` using the constructor's expiration convention
(naive UTC for SDK refreshes), or ``None`` when unknown.

.. code-block:: python

    import dropbox

    # Load refresh credentials separately from your application's secure storage.
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
        app_secret=app_secret,
    )
    dbx.users_get_current_account()  # Automatically refreshes when needed.
    snapshot = dbx.get_access_token_snapshot()
    if snapshot is not None:
        # Persist snapshot.access_token and snapshot.expires_at securely.
        next_dbx = dropbox.Dropbox(
            oauth2_access_token=snapshot.access_token,
            oauth2_access_token_expiration=snapshot.expires_at,
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret,
        )
        next_dbx.users_get_current_account()

An explicit ``dbx.refresh_access_token()`` also updates the cache. Reading a
snapshot never refreshes credentials: tokens may be expired or revoked, and an
unknown expiration does not imply unlimited lifetime. Store access tokens securely
and never log them. Snapshots never include refresh tokens.

``clone()``, ``with_path_root()``, ``as_user()``, and ``as_admin()`` copy the cached
credentials at creation. Each client subsequently refreshes independently;
unlike the .NET SDK, these clients do not share mutable credential state.
Concurrent refreshes remain independent requests; each successful completion
publishes a complete token/expiration pair, and failures preserve the cache.

Reliable File Transfers
=======================

Use ``dropbox.file_transfer`` when copying Dropbox files to or from local
storage and you want retry, progress, validation, byte/file targets, stream/file
sources, and optional parallel ranged transfers around the generated
``files_*`` methods.

.. code-block:: python

    import dropbox
    from dropbox import files
    from dropbox.file_transfer import (
        DownloadOptions,
        File,
        FileUpload,
        Uploader,
        UploadOptions,
        Downloader,
    )

    dbx = dropbox.Dropbox("YOUR_ACCESS_TOKEN")

    Downloader(dbx).download(
        "/large-file.bin",
        File("large-file.bin"),
        DownloadOptions(parallel_downloads=4),
    )

    Uploader(dbx).upload(
        FileUpload("large-file.bin"),
        files.CommitInfo("/large-file.bin", mode=files.WriteMode.overwrite),
        UploadOptions(parallel_uploads=4),
    )

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
