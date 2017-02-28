#!/bin/sh
if [ -z $1 ]; then
    echo "error: $0 needs a version number as argument. Current version: `python -c 'import dropbox; print(dropbox.__version__)'`";
else
    perl -pi -e "s/^__version__.*/__version__ = '$1'/g" dropbox/dropbox.py
fi
