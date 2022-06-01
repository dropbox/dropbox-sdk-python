#!/bin/sh
# The script is meant for SDK release on Github. You need write permission on https://github.com/dropbox/dropbox-sdk-python to run this script properly.

if [ -z $1 ]; then
    echo "error: $0 needs a version number as argument.";
    exit 1
else
    set -ex
    NEW_VERSION=$1

    git checkout main
    git reset --hard HEAD
    git checkout -b "tmp-release-${NEW_VERSION}"

    perl -pi -e "s/^__version__ = .*$/__version__ = '$1'/g" dropbox/dropbox_client.py
    perl -pi -e 's/(\?branch=)main$/\1\v'$1'/g ;' -e 's/(\?version=)latest$/\1\stable/g ;' -e 's/(\/en\/)latest(\/)$/\1\stable\2/g ;' -e 's/(\[Latest) (Documentation\])$/\1 Release \2/g ;' README.rst

    git add -u
    git commit -m "${NEW_VERSION} release"
    git tag "v${NEW_VERSION}" -m "${NEW_VERSION} release"

    git checkout main
    git branch -D "tmp-release-${NEW_VERSION}"

    git push origin
    git push origin --tags
fi
