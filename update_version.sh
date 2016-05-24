#!/bin/sh
if [ -z $1 ]; then echo "error: $0 needs a version number as argument."; fi
sed -i "s/^__version__.*/__version__ = '$1'/g" dropbox/dropbox.py
