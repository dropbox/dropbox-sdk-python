#!/bin/sh
if [ -z $1 ]; then
    echo "error: $0 needs a version number as argument. Current version: `python -c 'import dropbox; print(dropbox.__version__)'`";
    exit 1
else
    set -ex
    perl -pi -e "s/^__version__ = .*$/__version__ = '$1'/g" dropbox/dropbox.py
    perl -pi -e 's/(\?branch=)master$/\1\v'$1'/g ;' -e 's/(\?version=)latest$/\1\stable/g ;' -e 's/(\/en\/)latest(\/)$/\1\stable\2/g ;' -e 's/(\[Latest) (Documentation\])$/\1 Release \2/g ;' README.rst
fi
