# Upgrading the Dropbox SDK

This document is designed to show you how to upgrade to the latest version of the SDK accomodating any breaking changes introduced by major version updates.
If you find any issues with either this guide on upgrading or the changes introduced in the new version, please see [CONTRIBUTING.md](CONTRIBUTING.md)

# Upgrading from v10.X.X to v11.0.0
The major change that happened in this new version is that we regenerated the client files using Stone 3.2.0,
so relative imports are removed from the generated client files.
This created some issues with the imports in the non-generated files in `dropbox/`.
As a result, we renamed `dropbox.dropbox` to
`dropbox.dropbox_client`. If you used to do imports like `dropbox.dropbox.foo`, such imports need to be changed to `dropbox.dropbox_client.foo`.
However, we preserved the imports in `dropbox/__init__.py`, so imports like `from dropbox import DropboxOAuth2FlowNoRedirect`,
`from dropbox import Dropbox` will continue to work.
