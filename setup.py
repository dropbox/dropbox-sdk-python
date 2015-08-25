# Ensure setuptools is available
import sys

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup

install_reqs = ['urllib3',
                'requests>=2.5.1',
                'six>=1.3.0']
assert sys.version_info >= (2, 6), "We only support Python 2.6+"

with open('LICENSE') as f:
  license = f.read()

dist = setup(
    name='dropbox',
    version='3.13',
    description='Official Dropbox API Client',
    author='Dropbox',
    author_email='dev-platform@dropbox.com',
    url='http://www.dropbox.com/developers',
    install_requires=install_reqs,
    license=license,
    zip_safe=False,
    packages=['dropbox'],
    package_data={'dropbox': ['trusted-certs.crt']},
    platforms=['CPython 2.6', 'CPython 2.7'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
