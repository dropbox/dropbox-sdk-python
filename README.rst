Dropbox Python SDK
==================

.. image:: https://travis-ci.org/dropbox/dropbox-sdk-python.svg?branch=v10.1.0
    :target: https://travis-ci.org/dropbox/dropbox-sdk-python

.. image:: https://readthedocs.org/projects/dropbox-sdk-python/badge/?version=stable
    :target: https://dropbox-sdk-python.readthedocs.org/en/stable/
    :alt: [Latest Release Documentation]

.. image:: https://img.shields.io/pypi/v/dropbox.svg
    :target: https://pypi.python.org/pypi/dropbox
    :alt: [Latest Release Version]

.. image:: https://img.shields.io/pypi/l/dropbox.svg
    :target: http://opensource.org/licenses/MIT
    :alt: [Latest Release License]

.. image:: https://img.shields.io/pypi/pyversions/dropbox.svg
    :target: https://pypi.python.org/pypi/dropbox
    :alt: [Latest Release Supported Python Versions]

.. image:: https://img.shields.io/pypi/implementation/dropbox.svg
    :target: https://pypi.python.org/pypi/dropbox
    :alt: [Latest Release Supported Python Implementations]

.. image:: https://img.shields.io/pypi/status/dropbox.svg
    :target: https://pypi.python.org/pypi/dropbox
    :alt: [Latest Release Development Stage]

A Python SDK for integrating with the Dropbox API v2. Compatible with Python 2.7 and 3.4+. Documentation is available on `Read the Docs <http://dropbox-sdk-python.readthedocs.org/>`_.

Installation
------------

Create an app at https://dropbox.com/developers/apps

Install via `pip <https://pip.pypa.io/>`_:

.. code-block:: console

    $ pip install dropbox

Install from source:

.. code-block:: console

    $ git clone git://github.com/dropbox/dropbox-sdk-python.git
    $ cd dropbox-sdk-python
    $ python setup.py install

After installation, to get started, follow one of our examples or read the documentation on `Read the Docs <http://dropbox-sdk-python.readthedocs.org/>`_.

Authentication
--------------

All requests need to be made with an OAuth 2 access token. To get started, once you've created an app, you can go to the app's console and generate an access
token for your own Dropbox account for development.  You can also find a variety of examples outlining different authorization flows under:

`example/oauth <http://github.com/dropbox/dropbox-sdk-python/tree/master/example/oauth/>`_


Example Applications
--------------------

- `updown <http://github.com/dropbox/dropbox-sdk-python/tree/master/example/updown.py>`_ - A sample application that demonstrates simple file upload and download

Contributing
------------

Contributions to this SDK are always welcome and encouraged!

See the `CONTRIBUTING <http://github.com/dropbox/dropbox-sdk-python/blob/master/CONTRIBUTING.rst>`_ doc for more information

License
-------
MIT - See the `LICENSE <http://github.com/dropbox/dropbox-sdk-python/blob/master/LICENSE>`_ for more information
