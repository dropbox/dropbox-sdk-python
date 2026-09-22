# Contributing to the Dropbox SDK for Python
We value and rely on the feedback from our community. This comes in the form of bug reports, feature requests, and general guidance. We welcome your issues and pull requests and try our hardest to be timely in both response and resolution. Please read through this document before submitting issues or pull requests to ensure we have the necessary information to help you resolve your issue.

## Filing Bug Reports
You can file a bug report on the [GitHub Issues][issues] page.

1. Search through existing issues to ensure that your issue has not been reported. If it is a common issue, there is likely already an issue.

2. Please ensure you are using the latest version of the SDK. While this may be a valid issue, we only will fix bugs affecting the latest version and your bug may have been fixed in a newer version.

3. Provide as much information as you can regarding the language version, SDK version, and any other relevant information about your environment so we can help resolve the issue as quickly as possible.

## Submitting Pull Requests

We are more than happy to recieve pull requests helping us improve the state of our SDK. You can open a new pull request on the [GitHub Pull Requests][pr] page.

1. Please ensure that you have read the [License][license], [Code of Conduct][coc] and have signed the [Contributing License Agreement (CLA)][cla].

2. Please add tests confirming the new functionality works. Pull requests will not be merged without passing continuous integration tests unless the pull requests aims to fix existing issues with these tests.

## Updating Generated Code

Generated code can be updated by running the following code:

```
$ pip install -r requirements.txt
$ git submodule init
$ git submodule update --remote --recursive
$ python generate_base_client.py
```

Note: Stone updates must be made by updating `requirements.txt` as it is no longer a submodule.

## Testing the Code

We use the [`tox`](https://tox.readthedocs.org/) package to run tests. To install and run the unit tests, you can use:

```
$ pip install tox
$ tox
```

Or if you would like to specify a specific target to run you can run this:

```
$ tox -e {TARGET}
```

If you want to run the integration tests, you can use the following:

```
$ export DROPBOX_REFRESH_TOKEN={fill in refresh token}
$ export DROPBOX_APP_KEY={fill in app key}
$ export DROPBOX_APP_SECRET={fill in app secret}
$ export DROPBOX_TEAM_TOKEN={fill in team token}
$ export DROPBOX_TOKEN={fill in access token}
$ tox -e test_integration
```
Note: If you do not have all of these tokens available, we run integration tests as a part of pull request validation and you are able to rely on those if you are unable to obtain yourself.

We do recommend developing in a virtual environment in order to ensure you have a clean testing environment.

If you want to build the documentation locally, you can run this:

```
$ tox -e docs
```

The documentation will be built into `build/html`.

## Cutting New Versions (for Dropboxers)

Repository admins can cut a new version from the GitHub Actions page:

1. Select the **Release** workflow and click **Run workflow**.
2. Select the `main` branch, choose the `pypi` destination, and enter the version as `X.Y.Z` (without the `v` prefix).
3. Run the workflow. It validates and tests the exact `main` commit, creates the `vX.Y.Z` tag, builds and verifies the distributions from that tag, publishes them to PyPI with Trusted Publishing, and then creates the GitHub Release with generated release notes.

Creating a GitHub release manually with a `vX.Y.Z` tag remains supported and automatically publishes version `X.Y.Z` to PyPI.

To validate Trusted Publishing without making a production release, run the same workflow manually from `main` with the `testpypi` destination. The workflow publishes the checked artifacts only to TestPyPI with a unique `X.Y.Z.dev<run-id>` version; it does not create a tag or GitHub Release.

TestPyPI requires its own one-time Trusted Publisher configuration; the production PyPI configuration does not apply there. Configure the `dropbox` project (or a pending publisher if the project does not exist yet) for GitHub owner `dropbox`, repository `dropbox-sdk-python`, workflow `pypiupload.yml`, and no environment restriction.

[issues]: https://github.com/dropbox/dropbox-sdk-python/issues
[pr]: https://github.com/dropbox/dropbox-sdk-python/pulls
[coc]: https://github.com/dropbox/dropbox-sdk-python/blob/main/CODE_OF_CONDUCT.md
[license]: https://github.com/dropbox/dropbox-sdk-python/blob/main/LICENSE
[cla]: https://opensource.dropbox.com/cla/
