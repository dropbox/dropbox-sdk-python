# Don't import unicode_literals because of a bug in py2 setuptools
# where package_data is expected to be str and not unicode.
from __future__ import absolute_import, division, print_function

import os
import sys

# Ensure setuptools is available
try:
    from ez_setup import use_setuptools
    use_setuptools()
except ImportError:
    # Try to use ez_setup, but if not, continue anyway. The import is known
    # to fail when installing from a tar.gz.
    print('Could not import ez_setup', file=sys.stderr)

from setuptools import setup

dbx_mod_path = os.path.join(os.path.dirname(__file__), 'dropbox/dropbox.py')
line = '= "UNKNOWN"'
for line in open(dbx_mod_path):
    if line.startswith('__version__'):
        break
version = eval(line.split('=', 1)[1].strip())  # pylint: disable=eval-used

install_reqs = [
    'requests >= 2.5.1, != 2.6.1',
    'six >= 1.3.0',
    'urllib3',
]

setup_requires = [
    'pytest-runner',
]

test_reqs = [
    'pytest',
]

# WARNING: This imposes limitations on test/requirements.txt such that the
# full Pip syntax is not supported. See also
# <http://stackoverflow.com/questions/14399534/>.
with open('test/requirements.txt') as f:
    test_reqs += f.read().splitlines()

with open('LICENSE') as f:
    LICENSE = f.read()

with open('README.rst') as f:
    README = f.read()

dist = setup(
    name='dropbox',
    version=version,
    description='Official Dropbox API Client',
    author='Dropbox',
    author_email='dev-platform@dropbox.com',
    url='http://www.dropbox.com/developers',
    install_requires=install_reqs,
    setup_requires=setup_requires,
    tests_require=test_reqs,
    license=LICENSE,
    zip_safe=False,
    packages=['dropbox'],
    package_data={'dropbox': ['trusted-certs.crt']},
    long_description=README,
    platforms=[
        'CPython 2.7',
        'CPython 3.3',
        'CPython 3.4',
        'CPython 3.5',
        'CPython 3.6',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
