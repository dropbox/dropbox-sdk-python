#!/bin/bash

# If a test suite returns an error, do not continue to the next one.
set -e

echo "Running tests for dropbox package"
PYTHONPATH=.. python2.7 -m pytest

echo
echo "Running tests for dropbox package using Python 3"
PYTHONPATH=.. python3 -m pytest

