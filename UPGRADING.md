# Upgrading the Dropbox SDK

This document is designed to show you how to upgrade to the latest version of the SDK accomodating any breaking changes introduced by major version updates.
If you find any issues with either this guide on upgrading or the changes introduced in the new version, please see [CONTRIBUTING.md](CONTRIBUTING.md)

# Upgrading to v12.0.0
* The SDK no longer provides its own CA bundle to verify TLS connections. It will continue to verify connections through the `requests` library, which makes use of [`certifi`](https://github.com/certifi/python-certifi). You may still provide your own bundle through the `ca_certs` parameter of the `Dropbox` classes and of the `create_session` function (see the [documentation](https://dropbox-sdk-python.readthedocs.io/en/latest/api/dropbox.html) for details).
* This will be the last major version to support Python 2.

# Upgrading from v10.X.X to v11.0.0
The major change that happened in this new version is that we regenerated the client files using Stone 3.2.0,
so relative imports are removed from the generated client files.
This created some issues with the imports in the non-generated files in `dropbox/`.
As a result, we renamed `dropbox.dropbox` to
`dropbox.dropbox_client`. If you used to do imports like `dropbox.dropbox.foo`, such imports need to be changed to `dropbox.dropbox_client.foo`.
However, we preserved the imports in `dropbox/__init__.py`, so imports like `from dropbox import DropboxOAuth2FlowNoRedirect`,
`from dropbox import Dropbox` will continue to work.
